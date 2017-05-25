from flask import redirect
from flask import render_template, abort
from flask import url_for

from uchan import app
from uchan.lib.cache import board_cache, site_cache
from uchan.lib.model import BoardConfigModel, BoardModel, CatalogModel
from uchan.lib.moderator_request import get_authed, request_moderator
from uchan.lib.utils import valid_id_range
from uchan.lib.service import posts_service, moderator_service, board_service


def get_board_view_params(board_config: BoardConfigModel, mode, board_name, additional_page_details=None):
    global_posting_enabled = site_cache.find_site_config().get('file_posting_enabled')
    file_posting_enabled = board_config.file_posting and global_posting_enabled

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
        'full_name': board_config.full_name,
        'description': board_config.description,
        'pages': board_config.pages,
        'file_posting_enabled': file_posting_enabled,
        'page_details': details
    }


def show_moderator_buttons(board_id):
    if get_authed():
        moderator = request_moderator()
        if moderator_service.moderates_board_id(moderator, board_id):
            return True

    return False


@app.route('/<string(maxlength=20):board_name>/')
@app.route('/<string(maxlength=20):board_name>/<int:page>')
def board(board_name, page=None):
    board: BoardModel = board_service.find_board(board_name, include_config=True)

    if not board:
        abort(404)

    # Page 1 is argument-less
    if page == 1:
        return redirect(url_for('board', board_name=board_name))

    if page is None:
        page = 1

    if page <= 0 or page > board.config.pages:
        abort(404)

    # Index starts from 0
    index = page - 1

    board_page = posts_service.get_board_page(board, index)

    # TODO: don't use the board id
    show_mod_buttons = show_moderator_buttons(board.id)

    return render_template('board.html', board=board, board_page=board_page, page_index=index,
                           show_moderator_buttons=show_mod_buttons,
                           **get_board_view_params(board.config, 'board', board_name))


@app.route('/<string(maxlength=20):board_name>/read/<int:thread_refno>')
def view_thread(board_name, thread_refno):
    valid_id_range(thread_refno)

    board: BoardModel = board_service.find_board(board_name, include_config=True)
    if not board:
        abort(404)

    thread = posts_service.find_thread_by_board_thread_refno_with_posts(board, thread_refno)
    if not thread:
        abort(404)

    additional_page_details = {
        'threadRefno': thread.refno
    }
    if thread.locked:
        additional_page_details['locked'] = True
    if thread.sticky:
        additional_page_details['sticky'] = True

    # TODO: don't use the board id
    show_mod_buttons = show_moderator_buttons(thread.board.id)

    return render_template('thread.html', thread=thread, board=thread.board,
                           show_moderator_buttons=show_mod_buttons,
                           **get_board_view_params(board.config, 'thread', board_name, additional_page_details))


@app.route('/<string(maxlength=20):board_name>/catalog')
def board_catalog(board_name):
    board: BoardModel = board_service.find_board(board_name, include_config=True)
    if not board:
        abort(404)

    catalog: CatalogModel = posts_service.get_catalog(board)

    return render_template('catalog.html', board=board, catalog=catalog,
                           **get_board_view_params(board.config, 'catalog', board_name))
