from flask import render_template, abort, redirect, url_for

from uchan import app, g
from uchan.lib import roles
from uchan.lib.moderator_request import get_authed, request_moderator
from uchan.view.board import get_page_details


@app.route('/<string(maxlength=20):board_name>/view/<int:thread_id>')
def view_thread(board_name, thread_id):
    if thread_id <= 0 or thread_id > 2 ** 32:
        abort(400)

    board_config_cached = g.board_cache.find_board_config_cached(board_name)
    if not board_config_cached:
        abort(404)

    thread_cached = g.posts_cache.find_thread_cached(thread_id)

    if thread_cached and thread_cached.board.name == board_name:
        show_moderator_buttons = get_authed() and g.moderator_service.has_role(request_moderator(), roles.ROLE_ADMIN)

        page_details = get_page_details('thread', board_name)
        page_details['threadId'] = thread_cached.id
        if board_config_cached.board_config.file_posting_enabled:
            page_details['filePostingEnabled'] = True
        if thread_cached.locked:
            page_details['locked'] = True
        if thread_cached.sticky:
            page_details['sticky'] = True

        return render_template('thread.html', thread=thread_cached, board=thread_cached.board,
                               board_config=board_config_cached.board_config, show_moderator_buttons=show_moderator_buttons,
                               page_details=page_details)
    else:
        abort(404)
