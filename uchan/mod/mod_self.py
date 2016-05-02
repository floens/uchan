from flask import render_template, request, flash, redirect, url_for

from uchan import g
from uchan.lib import ArgumentError
from uchan.lib.mod_log import mod_log
from uchan.lib.moderator_request import request_moderator
from uchan.mod import mod
from uchan.view import with_token


@mod.route('/mod_self')
def mod_self():
    moderator = request_moderator()

    board_links = []
    for board in moderator.boards:
        board_links.append((board.name, url_for('board', board_name=board.name)))

    return render_template('mod_self.html', moderator=moderator, board_links=board_links)


@mod.route('/mod_self/change_password', methods=['POST'])
@with_token()
def mod_self_password():
    moderator = request_moderator()

    old_password = request.form['old_password']
    new_password = request.form['new_password']

    if not g.moderator_service.check_password_validity(new_password):
        flash('Invalid password')
        return redirect(url_for('.mod_self'))

    try:
        g.moderator_service.change_password(moderator, old_password, new_password)
        flash('Changed password')
        mod_log('password changed')
    except ArgumentError as e:
        flash(e.message)

    return redirect(url_for('.mod_self'))
