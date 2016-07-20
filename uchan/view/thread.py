from flask import redirect
from flask import render_template, abort
from flask import url_for

from uchan import app, g
from uchan.lib.moderator_request import get_authed, request_moderator


def get_board_view_params(board_config, mode, board_name, additional_page_details=None):
    global_posting_enabled = g.site_cache.find_site_config().get('file_posting_enabled')
    file_posting_enabled = board_config.get('file_posting_enabled') and global_posting_enabled

    details = {
        'mode': mode,
        'boardName': board_name,
        'postEndpoint': url_for('post')
    }
    if file_posting_enabled:
        details['filePostingEnabled'] = file_posting_enabled
    if additional_page_details:
        details.update(additional_page_details)

    return {
        'full_name': board_config.get('full_name'),
        'description': board_config.get('description'),
        'pages': board_config.get('pages'),
        'file_posting_enabled': file_posting_enabled,
        'page_details': details
    }


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

    return render_template('board.html', board=board_cached.board, threads=board_cached.threads,
                           **get_board_view_params(board_config, 'board', board_name),
                           show_moderator_buttons=show_moderator_buttons(board_cached.board.id),
                           page_index=page)


@app.route('/<string(maxlength=20):board_name>/view/<int:thread_refno>')
def view_thread(board_name, thread_refno):
    if thread_refno <= 0 or thread_refno > 2 ** 32:
        abort(400)

    board_config = g.board_cache.find_board_config(board_name)
    if not board_config:
        abort(404)

    thread_cached = g.posts_cache.find_thread_cached(board_name, thread_refno)

    if not thread_cached or thread_cached.board.name != board_name:
        abort(404)

    additional_page_details = {
        'threadId': thread_cached.id
    }
    if thread_cached.locked:
        additional_page_details['locked'] = True
    if thread_cached.sticky:
        additional_page_details['sticky'] = True

    return render_template('thread.html', thread=thread_cached, board=thread_cached.board,
                           **get_board_view_params(board_config, 'thread', board_name, additional_page_details),
                           show_moderator_buttons=show_moderator_buttons(thread_cached.board.id))


@app.route('/<string(maxlength=20):board_name>/catalog')
def board_catalog(board_name):
    board_config = g.board_cache.find_board_config(board_name)
    if not board_config:
        abort(404)

    board_cached = g.posts_cache.find_board_cached(board_name)
    if not board_cached:
        abort(404)

    return render_template('catalog.html', board=board_cached.board, threads=board_cached.threads,
                           **get_board_view_params(board_config, 'catalog', board_name))
