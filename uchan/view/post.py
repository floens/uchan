from time import sleep

from flask import request, abort, redirect, url_for, render_template, jsonify

from uchan import app, g
from uchan.lib import BadRequestError, ArgumentError
from uchan.lib.moderator_request import get_authed_moderator, get_authed
from uchan.lib.service.posts_service import RequestBannedException, RequestSuspendedException
from uchan.lib.tasks.post_task import PostDetails, ManagePostDetails, manage_post_task, post_task, post_check_task
from uchan.view import check_csrf_referer


@app.route('/post', methods=['POST'])
def post():
    form = request.form

    if not check_csrf_referer(request):
        abort(400)

    site_config = g.site_cache.find_site_config_cached()
    if not site_config.posting_enabled:
        raise BadRequestError('Posting is disabled')

    # Gather params
    thread_id_raw = form.get('thread', None)
    thread_id = None
    if thread_id_raw is not None:
        try:
            thread_id = int(thread_id_raw)
            if thread_id <= 0 or thread_id > 2 ** 32:
                abort(400)
        except ValueError:
            abort(400)

    board_name = form.get('board', None)
    if not board_name:
        abort(400)

    text = form.get('comment', None)
    if not text:
        text = None
    name = form.get('name', None)
    if not name:
        name = None
    subject = form.get('subject', None)
    if not subject:
        subject = None
    password = form.get('password', None)
    if not password:
        password = None

    file = request.files.get('file', None)
    has_file = file is not None and file.filename is not None and len(file.filename) > 0

    if has_file and not site_config.file_posting_enabled:
        raise BadRequestError('File posting is disabled')

    # ip4 of the request
    ip4 = g.ban_service.get_request_ip4()

    post_details = PostDetails(form, board_name, thread_id, text, name, subject, password, has_file, ip4)

    # Queue the post check task
    try:
        post_check_task.delay(post_details).get()
    except RequestBannedException:
        raise BadRequestError('You are banned')
    except RequestSuspendedException:
        raise BadRequestError('You must wait before posting again')
    except ArgumentError as e:
        raise BadRequestError(e.message)

    upload_queue_files = None
    try:
        # If a image was uploaded validate it and upload it to the cdn
        # Then if that's complete, send a task off to the workers to insert the details in the db
        if has_file:
            thumbnail_size = 128 if thread_id else 256
            try:
                post_details.uploaded_file, upload_queue_files = g.file_service.handle_upload(file, thumbnail_size)
            except ArgumentError as e:
                raise BadRequestError(e.message)

        # Queue the post task
        try:
            board_name, thread_id, post_refno = post_task.delay(post_details).get()
        except ArgumentError as e:
            raise BadRequestError(e.message)
    finally:
        if upload_queue_files is not None:
            # Clean up the files in the upload queue
            g.file_service.clean_up_queue(upload_queue_files)

    if request.is_xhr:
        return jsonify({
            'boardName': board_name,
            'threadId': thread_id,
            'postRefno': post_refno
        })
    else:
        return redirect(url_for('view_thread', board_name=board_name, thread_id=thread_id) + '#p' + str(post_refno))


@app.route('/post_manage', methods=['POST'])
def post_manage():
    form = request.form

    if not check_csrf_referer(request):
        abort(400)

    post_id = form.get('post_id', type=int)
    if post_id is not None and (post_id <= 0 or post_id > 2 ** 32):
        abort(404)

    thread_id = form.get('thread_id', type=int)
    if thread_id is None or thread_id <= 0 or thread_id > 2 ** 32:
        abort(400)

    password = form.get('password', None)
    if not password or len(password) > g.posts_service.MAX_PASSWORD_LENGTH:
        password = None

    ip4 = g.ban_service.get_request_ip4()

    details = ManagePostDetails(thread_id, post_id, ip4)
    mode_string = form.get('mode')
    success_message = 'Success!'
    if mode_string == 'delete':
        details.mode = ManagePostDetails.DELETE
        details.password = password
        success_message = 'Post deleted'
    elif mode_string == 'report':
        details.mode = ManagePostDetails.REPORT
        success_message = 'Post reported'
    elif mode_string == 'toggle_sticky':
        details.mode = ManagePostDetails.TOGGLE_STICKY
        success_message = 'Toggled sticky'
    elif mode_string == 'toggle_locked':
        details.mode = ManagePostDetails.TOGGLE_LOCKED
        success_message = 'Toggled locked'
    else:
        abort(400)

    moderator = get_authed_moderator() if get_authed() else None
    if moderator is not None:
        details.mod_id = moderator.id

    try:
        manage_post_task.delay(details).get()
    except RequestBannedException:
        raise BadRequestError('You are banned')

    return render_template('message.html', message=success_message)
