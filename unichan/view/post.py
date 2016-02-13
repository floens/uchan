from flask import request, abort, redirect, url_for, render_template

from unichan import app
from unichan.lib import BadRequestError
from unichan.lib.moderator_request import get_authed_moderator
from unichan.lib.tasks.post_task import PostDetails, ManagePostDetails, manage_post_task, post_task
from unichan.view import check_csrf_referer


@app.route('/post', methods=['POST'])
def post():
    form = request.form

    if not check_csrf_referer(request):
        abort(400)

    thread_id_raw = form.get('thread', None)
    thread_id = None
    if thread_id_raw is not None:
        try:
            thread_id = int(thread_id_raw)
            if thread_id <= 0:
                abort(400)
        except ValueError:
            abort(400)

    board_name = form.get('board', None)
    if not board_name:
        abort(400)

    text = form.get('text', None)
    name = form.get('name', None)
    subject = form.get('subject', None)
    password = form.get('password', None)
    if not password:
        password = None

    board_name, thread_id = post_task.delay(PostDetails(board_name, thread_id, text, name, subject, password)).get()

    return redirect(url_for('view_thread', board_name=board_name, thread_id=thread_id))


@app.route('/post_manage', methods=['POST'])
def post_manage():
    form = request.form

    if not check_csrf_referer(request):
        abort(400)

    post_id = form.get('post_id', type=int)
    if not post_id or post_id <= 0:
        raise BadRequestError('No post selected')

    password = form.get('password', None)
    if not password:
        password = None

    details = ManagePostDetails(post_id)
    mode_string = form.get('mode')
    success_message = 'Success!'
    if mode_string == 'delete':
        details.mode = ManagePostDetails.DELETE
        details.password = password
        success_message = 'Post deleted'
    elif mode_string == 'report':
        details.mode = ManagePostDetails.REPORT
        success_message = 'Post reported'
    else:
        abort(400)

    moderator = get_authed_moderator()
    if moderator is not None:
        details.mod_id = moderator.id

    try:
        manage_post_task.delay(details).get()
    except BadRequestError as e:
        return render_template('error.html', message=e.args[0])

    return render_template('message.html', message=success_message)
