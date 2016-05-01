from flask import render_template, abort, redirect, url_for

from uchan import app
from uchan import g
from uchan.lib import roles
from uchan.lib.moderator_request import get_authed, request_moderator


def get_page_details(mode, board_name):
    return {
        'mode': mode,
        'boardName': board_name,
        'postEndpoint': url_for('post')
    }


@app.route('/<string(maxlength=20):board_name>/')
@app.route('/<string(maxlength=20):board_name>/<int:page>')
def board(board_name, page=None):
    board_config_cached = g.board_cache.find_board_config_cached(board_name)
    if not board_config_cached:
        abort(404)

    if page == 1:
        return redirect(url_for('board', board_name=board_name))

    if page is None:
        page = 1

    if page <= 0 or page > board_config_cached.board_config.pages:
        abort(404)

    page -= 1

    board_cached = g.posts_cache.find_board_cached(board_name, page)
    if not board_cached:
        abort(404)

    page_details = get_page_details('board', board_name)
    if board_config_cached.board_config.file_posting_enabled:
        page_details['filePostingEnabled'] = True

    show_moderator_buttons = get_authed() and g.moderator_service.has_role(request_moderator(), roles.ROLE_ADMIN)

    return render_template('board.html', board=board_cached.board, threads=board_cached.threads,
                           board_config=board_config_cached.board_config, page_index=page,
                           page_details=page_details, show_moderator_buttons=show_moderator_buttons)


@app.route('/<string(maxlength=20):board_name>/catalog')
def board_catalog(board_name):
    board_config_cached = g.board_cache.find_board_config_cached(board_name)
    if not board_config_cached:
        abort(404)

    board_cached = g.posts_cache.find_board_cached(board_name)
    if not board_cached:
        abort(404)

    page_details = get_page_details('catalog', board_name)

    return render_template('catalog.html', board=board_cached.board, threads=board_cached.threads,
                           board_config=board_config_cached.board_config, page_details=page_details)
