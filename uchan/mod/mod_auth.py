from flask import request, redirect, url_for, render_template, abort, flash

from uchan import g
from uchan.lib import ArgumentError
from uchan.lib.moderator_request import get_authed, unset_mod_authed, set_mod_authed, get_authed_moderator
from uchan.lib.proxy_request import get_request_ip4_str
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
                g.mod_logger.info('{} logged out'.format(get_authed_moderator().username))
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
                    g.mod_logger.info('{} log in username failed'.format(get_request_ip4_str()))
                else:
                    try:
                        mod_service.check_password(moderator, password)
                        set_mod_authed(moderator)
                        flash('Logged in')
                        g.mod_logger.info('{} {} logged in'.format(moderator.username, get_request_ip4_str()))
                    except ArgumentError:
                        g.mod_logger.info('{} {} log in password failed'.format(moderator.username, get_request_ip4_str()))
                        flash('Invalid username or password')

        return redirect(url_for('.mod_auth'))
    else:
        authed = get_authed()
        moderator = get_authed_moderator() if authed else None
        return render_template('auth.html', authed=authed, moderator=moderator)
