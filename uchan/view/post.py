from flask import request, abort, redirect, url_for, render_template, jsonify

from uchan import app, configuration
from uchan.filter.app_filters import time_remaining
from uchan.lib import validation
from uchan.lib.action_authorizer import RequestBannedException, RequestSuspendedException
from uchan.lib.cache import board_cache, site_cache
from uchan.lib.exceptions import BadRequestError, ArgumentError
from uchan.lib.model import PostResultModel
from uchan.lib.moderator_request import request_moderator, get_authed
from uchan.lib.proxy_request import get_request_ip4
from uchan.lib.service import board_service, file_service, posts_service, verification_service
from uchan.lib.tasks.post_task import PostDetails, ManagePostDetails, manage_post_task, execute_post_task, \
    execute_manage_post_task
from uchan.lib.utils import now, valid_id_range
from uchan.view import check_csrf_referer

MESSAGE_POSTING_DISABLED = 'Posting is disabled'
MESSAGE_FILE_POSTING_DISABLED = 'File posting is disabled'
MESSAGE_REQUEST_BANNED = 'You are [banned](/banned/)'
MESSAGE_REQUEST_SUSPENDED = 'You must wait {} before posting again'


@app.route('/post', methods=['POST'])
def post():
    # We don't have csrf tokens for session-less endpoints like this.
    # Do it another way, with a referer check.
    _check_headers()

    post_details = _gather_post_params()

    _check_post_settings(post_details.has_file)

    board_config = board_cache.find_board_config(post_details.board_name)
    if not board_config:
        abort(404)

    upload_queue_files = None
    try:
        # If a image was uploaded validate it and save it to the upload queue
        if post_details.has_file:
            upload_queue_files = _queue_file(post_details)

        # Queue the post task that inserts the details in the database
        try:
            post_result = _execute_post(post_details)
        except Exception as e:
            raise _convert_exception(e)

        # If that was successful, upload the file to the cdn from the upload queue
        if post_details.has_file:
            _upload_files(upload_queue_files)
    finally:
        # Clean up the files in the upload queue, if there was an error too
        if upload_queue_files:
            _clean_files(upload_queue_files)

    return _create_post_response(post_result)


def _convert_exception(exception):
    try:
        raise exception
    except RequestBannedException:
        raise BadRequestError(MESSAGE_REQUEST_BANNED)
    except RequestSuspendedException as e:
        raise BadRequestError(MESSAGE_REQUEST_SUSPENDED.format(time_remaining(now() + 1000 * e.suspend_time)))
    except ArgumentError as e:
        raise BadRequestError(e.message)
        # Throw original too, as a server error


def _check_headers():
    if not check_csrf_referer(request):
        raise BadRequestError('Bad referer header')


def _check_post_settings(has_file):
    site_config = site_cache.find_site_config()
    if not site_config.get('posting_enabled'):
        raise BadRequestError(MESSAGE_POSTING_DISABLED)

    if has_file and not site_config.get('file_posting_enabled'):
        raise BadRequestError(MESSAGE_FILE_POSTING_DISABLED)


def _gather_post_params() -> PostDetails:
    form = request.form

    # Gather params
    thread_refno_raw = form.get('thread', None)
    thread_refno = None
    if thread_refno_raw is not None:
        try:
            thread_refno = int(thread_refno_raw)
            valid_id_range(thread_refno)
        except ValueError:
            abort(400)

    board_name = form.get('board', None)
    if not validation.check_board_name_validity(board_name):
        abort(400)

    text = form.get('comment', None)
    name = form.get('name', None)
    subject = form.get('subject', None)
    password = form.get('password', None)

    # Convert empty strings to None
    if not text:
        text = None
    if not name:
        name = None
    if not subject:
        subject = None
    if not password:
        password = None

    file = request.files.get('file', None)
    has_file = file is not None and file.filename is not None and len(file.filename) > 0

    ip4 = get_request_ip4()

    with_mod = form.get('with_mod', default=False, type=bool)
    mod_id = None
    if with_mod:
        moderator = request_moderator() if get_authed() else None
        if moderator is not None:
            mod_id = moderator.id

    verification_data = verification_service.get_verification_data_for_request(request, ip4, 'post')

    return PostDetails(form, board_name, thread_refno, text, name, subject, password, has_file,
                       ip4, mod_id, verification_data)


def _execute_post(post_details) -> PostResultModel:
    return execute_post_task(post_details)


def _create_post_response(post_result):
    if request.is_xhr:
        return jsonify({
            'boardName': post_result.board_name,
            'threadRefno': post_result.thread_refno,
            'postRefno': post_result.post_refno
        })
    else:
        return redirect(url_for_post(post_result.board_name, post_result.thread_refno, post_result.post_refno))


def _queue_file(post_details):
    file = request.files['file']
    start_time = now()
    thumbnail_size = configuration.app.thumbnail_reply if post_details.thread_refno else configuration.app.thumbnail_op
    try:
        post_details.uploaded_file, upload_queue_files = file_service.prepare_upload(file, thumbnail_size)
    except ArgumentError as e:
        raise BadRequestError(e.message)
    post_details.file_time = now() - start_time
    return upload_queue_files


def _upload_files(upload_queue_files):
    file_service.do_upload(upload_queue_files)


def _clean_files(upload_queue_files):
    file_service.clean_up_queue(upload_queue_files)


@app.route('/post_manage', methods=['POST'])
def post_manage():
    form = request.form

    # We don't have csrf tokens for session-less endpoints like this.
    # Do it another way, with a referer check.
    _check_headers()

    details = _gather_manage_params()

    success_message = 'Success!'
    if details.mode == 'delete':
        details.mode = ManagePostDetails.DELETE
        success_message = 'Post deleted'
    elif details.mode == 'report':
        details.mode = ManagePostDetails.REPORT
        success_message = 'Post reported'
        data = verification_service.get_verification_data_for_request(request, details.ip4, 'report')
        details.report_verification_data = data
    elif details.mode == 'toggle_sticky':
        details.mode = ManagePostDetails.TOGGLE_STICKY
        success_message = 'Toggled sticky'
    elif details.mode == 'toggle_locked':
        details.mode = ManagePostDetails.TOGGLE_LOCKED
        success_message = 'Toggled locked'
    else:
        abort(400)

    try:
        execute_manage_post_task(details)
    except RequestBannedException:
        raise BadRequestError('You are [banned](/banned/)')

    return render_template('message.html', message=success_message)


def _gather_manage_params() -> ManagePostDetails:
    form = request.form

    board_name = form.get('board', None)
    if not validation.check_board_name_validity(board_name):
        abort(400)

    thread_refno = form.get('thread', type=int)
    valid_id_range(thread_refno)

    post_id = form.get('post_id', type=int)
    if not post_id:
        post_id = None

    if post_id is not None:
        valid_id_range(post_id)

    password = form.get('password', None)
    if not password:
        password = None

    if password and not validation.check_password_validity(password):
        abort(400)

    ip4 = get_request_ip4()

    mod_id = None
    if get_authed():
        mod_id = request_moderator().id

    mode_string = form.get('mode')

    return ManagePostDetails(board_name, thread_refno, post_id, ip4, mod_id, mode_string, password)


@app.route('/find_post/<int:post_id>')
def find_post(post_id):
    valid_id_range(post_id)

    post = posts_service.find_post(post_id)
    if post:
        return redirect(url_for_post(post.thread.board.name, post.thread.refno, post.refno))
    else:
        abort(404)


def url_for_post(board_name, thread_refno, post_id):
    return url_for('view_thread', board_name=board_name, thread_refno=thread_refno) + '#p' + str(post_id)


app.jinja_env.globals['url_for_post'] = url_for_post
