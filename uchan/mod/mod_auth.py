from flask import request, redirect, url_for, render_template, abort, flash

from uchan import g
from uchan.lib import ArgumentError
from uchan.lib.mod_log import mod_log
from uchan.lib.moderator_request import get_authed, unset_mod_authed, set_mod_authed, get_authed_moderator
from uchan.mod import mod
from uchan.view import check_csrf_token


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
                mod_log('logged out')
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
                    mod_log('log in with invalid username')
                else:
                    try:
                        mod_service.check_password(moderator, password)
                        set_mod_authed(moderator)
                        flash('Logged in')
                        mod_log('logged in')
                    except ArgumentError:
                        flash('Invalid username or password')
                        mod_log('log in with invalid password for username {}'.format(moderator.username))

        return redirect(url_for('.mod_auth'))
    else:
        authed = get_authed()
        moderator = get_authed_moderator() if authed else None
        return render_template('auth.html', authed=authed, moderator=moderator)
