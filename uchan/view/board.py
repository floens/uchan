from flask import render_template, abort, redirect, url_for

from uchan import app
from uchan import g
from uchan.lib.moderator_request import get_authed, request_moderator


def get_file_posting_enabled(board_config):
    global_posting_enabled = g.site_cache.find_site_config().get('file_posting_enabled')
    return board_config.get('file_posting_enabled') and global_posting_enabled


def get_page_details(mode, board_name, file_posting_enabled, thread_id=None):
    details = {
        'mode': mode,
        'boardName': board_name,
        'postEndpoint': url_for('post')
    }
    if file_posting_enabled:
        details['filePostingEnabled'] = file_posting_enabled
    if thread_id is not None:
        details['threadId'] = thread_id
    return details


def show_moderator_buttons(board_id):
    if get_authed():
        moderator = request_moderator()
        if g.moderator_service.moderates_board_id(moderator, board_id):
            return True

    return False


@app.route('/<string(maxlength=20):board_name>/')
@app.route('/<string(maxlength=20):board_name>/<int:page>')
def board(board_name, page=None):
    board_config = g.board_cache.find_board_config(board_name)
    if not board_config:
        abort(404)

    if page == 1:
        return redirect(url_for('board', board_name=board_name))

    if page is None:
        page = 1

    if page <= 0 or page > board_config.get('pages'):
        abort(404)

    page -= 1

    board_cached = g.posts_cache.find_board_cached(board_name, page)
    if not board_cached:
        abort(404)

    file_posting_enabled = get_file_posting_enabled(board_config)
    page_details = get_page_details('board', board_name, file_posting_enabled)

    return render_template('board.html', board=board_cached.board, threads=board_cached.threads,
                           full_name=board_config.get('full_name'),
                           description=board_config.get('description'),
                           pages=board_config.get('pages'),
                           page_index=page,
                           page_details=page_details,
                           file_posting_enabled=file_posting_enabled,
                           show_moderator_buttons=show_moderator_buttons(board_cached.board.id))


@app.route('/<string(maxlength=20):board_name>/catalog')
def board_catalog(board_name):
    board_config = g.board_cache.find_board_config(board_name)
    if not board_config:
        abort(404)

    board_cached = g.posts_cache.find_board_cached(board_name)
    if not board_cached:
        abort(404)

    file_posting_enabled = get_file_posting_enabled(board_config)
    page_details = get_page_details('catalog', board_name, file_posting_enabled)

    return render_template('catalog.html', board=board_cached.board, threads=board_cached.threads,
                           full_name=board_config.get('full_name'),
                           description=board_config.get('description'),
                           page_details=page_details)
