from flask import request, redirect, url_for, render_template, abort, flash

from uchan import g
from uchan.lib import roles, BadRequestError
from uchan.lib import ArgumentError, NoPermissionError
from uchan.lib.mod_log import mod_log
from uchan.lib.models import Board
from uchan.lib.moderator_request import request_moderator
from uchan.mod import mod
from uchan.view import check_csrf_token, with_token


def get_board_or_abort(board_name):
    if not board_name or len(board_name) > g.board_service.BOARD_NAME_MAX_LENGTH:
        abort(400)

    board = g.board_service.find_board(board_name)
    if not board:
        abort(404)
    return board


@mod.route('/mod_board')
def mod_boards():
    return render_template('mod_boards.html', moderator=request_moderator())


@mod.route('/mod_board/<board_name>', methods=['GET', 'POST'])
def mod_board(board_name):
    board = get_board_or_abort(board_name)

    moderator = request_moderator()
    if not g.moderator_service.moderates_board(moderator, board):
        raise NoPermissionError()

    g.moderator_service.has_board_role(moderator, board, roles.BOARD_ROLE_JANITOR)

    board_config_row = board.config
    board_config = g.config_service.load_config(board_config_row, moderator)

    if request.method == 'GET':
        return render_template('mod_board.html', board=board, board_config=board_config)
    else:
        form = request.form

        if not check_csrf_token(form.get('token')):
            abort(400)

        try:
            g.config_service.save_from_form(moderator, board_config, board_config_row, form)
            flash('Board config updated')
            mod_log('board /{}/ config updated'.format(board_name))
            g.board_cache.invalidate_board_config(board_name)
        except ArgumentError as e:
            flash(str(e))

        return redirect(url_for('.mod_board', board_name=board_name))


@mod.route('/mod_board/add', methods=['POST'])
@with_token()
def mod_board_add():
    board_name = request.form['board_name']

    board = Board()
    board.name = board_name

    try:
        g.moderator_service.user_create_board(request_moderator(), board)
        flash('Board added')
        mod_log('add board /{}/'.format(board_name))
    except ArgumentError as e:
        flash(e.message)
        return redirect(url_for('.mod_boards'))

    return redirect(url_for('.mod_board', board_name=board.name))


@mod.route('/mod_board/delete', methods=['POST'])
@with_token()
def mod_board_delete():
    board = get_board_or_abort(request.form['board_name'])

    try:
        g.board_service.delete_board(board)
        flash('Board deleted')
        mod_log('delete board /{}/'.format(board.name))
    except ArgumentError as e:
        flash(e.message)

    return redirect(url_for('.mod_boards'))
