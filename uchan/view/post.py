from typing import Tuple

from flask import abort, jsonify, redirect, render_template, request, url_for

from uchan import app, config
from uchan.filter.app_filters import page_formatting, time_remaining
from uchan.lib import validation
from uchan.lib.action_authorizer import (
    RequestBannedException,
    RequestSuspendedException,
)
from uchan.lib.exceptions import ArgumentError, BadRequestError
from uchan.lib.model import BoardModel, PostResultModel
from uchan.lib.moderator_request import get_authed, request_moderator
from uchan.lib.proxy_request import get_request_ip4
from uchan.lib.service import (
    board_service,
    file_service,
    post_manage_helper,
    posts_service,
    site_service,
    verification_service,
)
from uchan.lib.tasks.post_task import (
    ManagePostDetails,
    PostDetails,
    execute_manage_post_task,
    execute_post_task,
)
from uchan.lib.utils import now, valid_id_range
from uchan.view import check_csrf_referer

MESSAGE_POSTING_DISABLED = "Posting is disabled"
MESSAGE_FILE_POSTING_DISABLED = "File posting is disabled"
MESSAGE_REQUEST_BANNED = "You are [banned](/banned/)"
MESSAGE_REQUEST_SUSPENDED = "You must wait {} before posting again"


@app.route("/post", methods=["POST"])
def post():
    # We don't have csrf tokens for session-less endpoints like this.
    # Do it another way, with a referer check.
    _check_headers()

    board, post_details = _gather_post_params()

    r = _check_post_settings(board, post_details)
    if r:
        return r

    upload_queue_files_list = None
    try:
        # If a image was uploaded validate it and save it to the upload queue
        if post_details.has_files:
            upload_queue_files_list = _queue_files(post_details)

        # Queue the post task that inserts the details in the database
        try:
            post_result = _execute_post(post_details)
        except Exception as e:
            raise _convert_exception(e) from e

        # If that was successful, upload the file to the cdn from the upload queue
        if post_details.has_files:
            _upload_files(upload_queue_files_list)
    finally:
        # Clean up the files in the upload queue, if there was an error too
        if upload_queue_files_list:
            _clean_files(upload_queue_files_list)

    return _create_post_response(post_result)


def _convert_exception(exception):
    try:
        raise exception
    except RequestBannedException as e:
        raise BadRequestError(MESSAGE_REQUEST_BANNED) from e
    except RequestSuspendedException as e:
        raise BadRequestError(
            MESSAGE_REQUEST_SUSPENDED.format(
                time_remaining(now() + 1000 * e.suspend_time)
            )
        ) from e
    except ArgumentError as e:
        raise BadRequestError(e.message) from e
        # Throw original too, as a server error


def _check_headers():
    if not check_csrf_referer(request):
        raise BadRequestError("Bad referer header")


def _check_post_settings(board: BoardModel, post_details):
    site_config = site_service.get_site_config()
    if not site_config.posting_enabled:
        raise BadRequestError(MESSAGE_POSTING_DISABLED)

    if post_details.has_files and not site_config.file_posting:
        raise BadRequestError(MESSAGE_FILE_POSTING_DISABLED)

    if (
        post_details.has_files
        and len(_get_files_from_request()) > board.config.max_files
    ):
        raise BadRequestError(
            "No more than {} files are allowed.".format(board.config.max_files)
        )

    if (
        board.config.posting_verification_required
        and not verification_service.is_verified(request)
    ):
        method = verification_service.get_method()
        if method.verification_in_request(request):
            try:
                method.verify_request(request)
                verification_service.set_verified(request)
            except ArgumentError as e:
                raise BadRequestError(e) from e
        else:
            message = "Please verify here first before posting."

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                xhr_response = {
                    "error": True,
                    "message": page_formatting("[{}](_/verify/)".format(message)),
                }

                return jsonify(xhr_response), 400
            else:
                with_refresh = (
                    "[{}](_/verify/)\n\n**Refresh this page after verifying.**".format(
                        message
                    )
                )

                return (
                    render_template(
                        "error.html", message=with_refresh, with_retry=True
                    ),
                    400,
                )


def _gather_post_params() -> Tuple[BoardModel, PostDetails]:
    form = request.form

    # Gather params
    thread_refno_raw = form.get("thread", None)
    thread_refno = None
    if thread_refno_raw is not None:
        try:
            thread_refno = int(thread_refno_raw)
            valid_id_range(thread_refno)
        except ValueError:
            abort(400)

    board_name = form.get("board", None)
    if not validation.check_board_name_validity(board_name):
        abort(400)

    board = board_service.find_board(board_name)
    if not board:
        abort(404)

    text = form.get("comment", None)
    name = form.get("name", None)
    subject = form.get("subject", None)
    password = form.get("password", None)

    # Convert empty strings to None
    if not text:
        text = None
    if not name:
        name = None
    if not subject:
        subject = None
    if not password:
        password = None

    files = _get_files_from_request()
    has_files = len(files) > 0

    ip4 = get_request_ip4()

    with_mod = form.get("with_mod", default=False, type=bool)
    mod_id = None
    if with_mod:
        moderator = request_moderator() if get_authed() else None
        if moderator is not None:
            mod_id = moderator.id

    return board, PostDetails(
        form,
        board_name,
        thread_refno,
        text,
        name,
        subject,
        password,
        has_files,
        ip4,
        mod_id,
        None,
    )


def _execute_post(post_details) -> PostResultModel:
    return execute_post_task(post_details)


def _create_post_response(post_result):
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(
            {
                "boardName": post_result.board_name,
                "threadRefno": post_result.thread_refno,
                "postRefno": post_result.post_refno,
            }
        )
    else:
        return redirect(
            url_for_post(
                post_result.board_name, post_result.thread_refno, post_result.post_refno
            )
        )


def _queue_files(post_details):
    files = _get_files_from_request()

    start_time = now()
    thumbnail_size = (
        config.thumbnail_reply if post_details.thread_refno else config.thumbnail_op
    )

    uploaded_files = []
    upload_queue_files_list = []

    for file in files:
        try:
            uploaded_file, upload_queue_files = file_service.prepare_upload(
                file, thumbnail_size
            )
            uploaded_files.append(uploaded_file)
            upload_queue_files_list.append(upload_queue_files)
        except ArgumentError as e:
            raise BadRequestError(e.message) from e

    post_details.uploaded_files = uploaded_files
    post_details.file_time = now() - start_time

    return upload_queue_files_list


def _get_files_from_request():
    files = []
    for rec_file in request.files.getlist("file"):
        if (
            rec_file is not None
            and rec_file.filename is not None
            and len(rec_file.filename) > 0
        ):
            files.append(rec_file)
    return files


def _upload_files(upload_queue_files_list):
    for upload_queue_files in upload_queue_files_list:
        file_service.do_upload(upload_queue_files)


def _clean_files(upload_queue_files_list):
    for upload_queue_files in upload_queue_files_list:
        file_service.clean_up_queue(upload_queue_files)


@app.route("/post_manage", methods=["POST"])
def post_manage():
    # We don't have csrf tokens for session-less endpoints like this.
    # Do it another way, with a referer check.
    _check_headers()

    details = _gather_manage_params()

    success_message = "Success!"
    if details.mode == "delete":
        details.mode = ManagePostDetails.DELETE
        success_message = "Post deleted"
    elif details.mode == "report":
        if not details.post_id:
            raise BadRequestError(post_manage_helper.MESSAGE_NO_POST_ID)

        action = url_for(".post_manage")

        method = verification_service.get_method()

        retry_params = {
            "mode": "report",
            "board": details.board_name,
            "thread": details.thread_refno,
            "post_id": details.post_id,
        }

        if method.verification_in_request(request):
            try:
                method.verify_request(request)
                verification_service.set_verified(request)
            except ArgumentError as e:
                return respond_verification_required(action, e.message, retry_params)
        else:
            return respond_verification_required(
                action, "Please verify to report this post", retry_params
            )

        details.mode = ManagePostDetails.REPORT
        success_message = "Post reported"
    elif details.mode == "toggle_sticky":
        details.mode = ManagePostDetails.TOGGLE_STICKY
        success_message = "Toggled sticky"
    elif details.mode == "toggle_locked":
        details.mode = ManagePostDetails.TOGGLE_LOCKED
        success_message = "Toggled locked"
    else:
        abort(400)

    try:
        execute_manage_post_task(details)
    except RequestBannedException as e:
        raise BadRequestError("You are [banned](/banned/)") from e

    return render_template("message.html", message=success_message)


def respond_verification_required(action, message, form_params):
    method = verification_service.get_method()

    return render_template(
        "verification_required.html",
        action=action,
        message=message,
        form_params=form_params,
        method=method,
    )


def _gather_manage_params() -> ManagePostDetails:
    form = request.form

    board_name = form.get("board", None)
    if not validation.check_board_name_validity(board_name):
        abort(400)

    thread_refno = form.get("thread", type=int)
    valid_id_range(thread_refno)

    post_id = form.get("post_id", type=int)
    if not post_id:
        post_id = None

    if post_id is not None:
        valid_id_range(post_id)

    password = form.get("password", None)
    if not password:
        password = None

    if password and not validation.check_password_validity(password):
        abort(400)

    ip4 = get_request_ip4()

    mod_id = None
    if get_authed():
        mod_id = request_moderator().id

    mode_string = form.get("mode")

    return ManagePostDetails(
        board_name, thread_refno, post_id, ip4, mod_id, mode_string, password
    )


@app.route("/find_post/<int:post_id>")
def find_post(post_id):
    valid_id_range(post_id)

    post = posts_service.find_post(post_id)
    if post:
        return redirect(
            url_for_post(post.thread.board.name, post.thread.refno, post.refno)
        )
    else:
        abort(404)


def url_for_post(board_name, thread_refno, post_id):
    return (
        url_for("view_thread", board_name=board_name, thread_refno=thread_refno)
        + "#p"
        + str(post_id)
    )


app.jinja_env.globals["url_for_post"] = url_for_post
