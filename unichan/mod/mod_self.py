from flask import render_template, abort, request, flash, redirect, url_for

from unichan import g
from unichan.lib import ArgumentError
from unichan.lib.moderator_request import get_authed_moderator
from unichan.mod import mod
from unichan.view import with_token


@mod.route('/mod_self')
def mod_self():
    moderator = get_authed_moderator()

    return render_template('mod_self.html', moderator=moderator)


@mod.route('/mod_self/change_password', methods=['POST'])
@with_token()
def mod_self_password():
    moderator = get_authed_moderator()

    old_password = request.form['old_password']
    new_password = request.form['new_password']

    try:
        g.moderator_service.change_password(moderator, old_password, new_password)
        flash('Changed password')
    except ArgumentError as e:
        flash(e.message)

    return redirect(url_for('.mod_self'))
