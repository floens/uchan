from flask import request, redirect, url_for, render_template, abort, flash

from unichan import g
from unichan.lib import ArgumentError
from unichan.lib.moderator_request import get_authed, unset_mod_authed, set_mod_authed, get_authed_moderator
from unichan.mod import mod
from unichan.view import check_csrf_token


@mod.route('/')
def mod_index():
    return redirect(url_for('.mod_auth'))


@mod.route('/auth', methods=['GET', 'POST'])
def mod_auth():
    if request.method == 'POST':
        if not check_csrf_token(request.form.get('token')):
            abort(400)

        if get_authed():
            if request.form.get('deauth') == 'yes':
                unset_mod_authed()
        else:
            username = request.form['username']
            password = request.form['password']

            mod_service = g.moderator_service

            if not mod_service.check_username_validity(username) or not mod_service.check_password_validity(password):
                flash('Invalid username or password')
            else:
                moderator = mod_service.find_moderator_username(username)
                if not moderator:
                    flash('Invalid username or password')
                else:
                    try:
                        mod_service.check_password(moderator, password)
                        set_mod_authed(moderator)
                        flash('Logged in')
                    except ArgumentError:
                        flash('Invalid username or password')

        return redirect(url_for('.mod_auth'))
    else:
        authed = get_authed()
        moderator = get_authed_moderator() if authed else None
        return render_template('auth.html', authed=authed, moderator=moderator)
