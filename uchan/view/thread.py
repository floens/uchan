from flask import render_template, abort

from uchan import app, g
from uchan.view.board import get_page_details, show_moderator_buttons, get_file_posting_enabled


@app.route('/<string(maxlength=20):board_name>/view/<int:thread_id>')
def view_thread(board_name, thread_id):
    if thread_id <= 0 or thread_id > 2 ** 32:
        abort(400)

    board_config = g.board_cache.find_board_config(board_name)
    if not board_config:
        abort(404)

    file_posting_enabled = get_file_posting_enabled(board_config)

    thread_cached = g.posts_cache.find_thread_cached(thread_id)

    if not thread_cached or thread_cached.board.name != board_name:
        abort(404)

    page_details = get_page_details('thread', board_name, file_posting_enabled, thread_id=thread_cached.id)
    if thread_cached.locked:
        page_details['locked'] = True
    if thread_cached.sticky:
        page_details['sticky'] = True

    return render_template('thread.html', thread=thread_cached, board=thread_cached.board,
                           full_name=board_config.get('full_name'),
                           description=board_config.get('description'),
                           file_posting_enabled=file_posting_enabled,
                           show_moderator_buttons=show_moderator_buttons(thread_cached.board.id),
                           page_details=page_details)
