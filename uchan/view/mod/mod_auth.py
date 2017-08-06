from flask import request, redirect, url_for, render_template, abort, flash, session

from uchan import configuration
from uchan.lib import validation
from uchan.lib.exceptions import BadRequestError, ArgumentError
from uchan.lib.mod_log import mod_log
from uchan.lib.moderator_request import get_authed, unset_mod_authed, set_mod_authed, request_moderator
from uchan.lib.service import moderator_service, verification_service
from uchan.view import check_csrf_token, check_csrf_referer
from uchan.view.mod import mod


@mod.before_request
def mod_restrict():
    if (request.endpoint != 'mod.mod_auth' and request.endpoint != 'mod.mod_reg') and not get_authed():
        return mod_abort_redirect()


def mod_abort_redirect():
    return redirect(url_for('.mod_auth'))


@mod.route('/')
def mod_index():
    return redirect(url_for('.mod_auth'))


def verify_method():
    method = verification_service.get_method()
    try:
        method.verify_request(request)
    except ArgumentError as e:
        raise BadRequestError(e.message)


@mod.route('/auth', methods=['GET', 'POST'])
def mod_auth():
    if request.method == 'POST':
        return _mod_auth_post()
    else:
        authed = get_authed()
        moderator = request_moderator() if authed else None

        method = None
        if not authed:
            method = verification_service.get_method()

        return render_template('auth.html', authed=authed, moderator=moderator, method=method)


def _mod_auth_post():
    if get_authed():
        _mod_auth_deauth()
    else:
        _mod_auth_auth()

    return redirect(url_for('.mod_auth'))


def _mod_auth_auth():
    if not check_csrf_referer(request):
        raise BadRequestError('Bad referer header')

    verify_method()

    username = request.form['username']
    password = request.form['password']

    if not validation.check_username_validity(username) or not validation.check_password_validity(password):
        raise BadRequestError('Invalid username or password')
    else:
        moderator = moderator_service.find_moderator_username(username)
        if not moderator:
            mod_log('log in with invalid username')
            raise BadRequestError('Invalid username or password')
        else:
            try:
                moderator_service.check_password(moderator, password)
                set_mod_authed(moderator)
                flash('Logged in')
                mod_log('logged in')
            except ArgumentError:
                mod_log('log in with invalid password for username {}'.format(moderator.username))
                raise BadRequestError('Invalid username or password')


def _mod_auth_deauth():
    if request.form.get('deauth') == 'yes':
        if not check_csrf_token(request.form.get('token')):
            abort(400)

        mod_log('logged out')
        unset_mod_authed()
        session.clear()


@mod.route('/auth/reg', methods=['POST'])
def mod_reg():
    if not check_csrf_referer(request):
        raise BadRequestError('Bad referer header')

    verify_method()

    username = request.form['username']
    password = request.form['password']
    password_repeat = request.form['password_repeat']

    try:
        moderator = moderator_service.user_register(username, password, password_repeat)
        set_mod_authed(moderator)
    except ArgumentError as e:
        raise BadRequestError(e.message)

    return redirect(url_for('.mod_auth'))
