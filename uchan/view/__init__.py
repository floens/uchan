import random
import string
from functools import wraps
from urllib.parse import urlparse

from flask import json
from flask import send_from_directory, session, request, abort, url_for, render_template, jsonify
from markupsafe import escape, Markup

from uchan import app, configuration
from uchan.filter.app_filters import page_formatting
from uchan.lib import plugin_manager
from uchan.lib.cache import site_cache, board_cache, page_cache
from uchan.lib.service import page_service


class ExtraJavascript:
    def __init__(self):
        self.js = ''

    def add(self, js):
        self.js += js

    def gather(self):
        return self.js


@app.context_processor
def inject_variables():
    site_config = site_cache.find_site_config()

    all_boards = None
    if site_config.get('boards_top'):
        all_boards = board_cache.all_boards()

    footer_pages_cached = page_cache.find_pages_for_type_cached(page_service.TYPE_FOOTER_PAGE)
    footer_pages = footer_pages_cached.pages if footer_pages_cached else []

    extra_javascript = ExtraJavascript()
    plugin_manager.execute_hook('extra_javascript', extra_javascript)

    header_links = [
        ('mod', url_for('mod.mod_auth')),
    ]

    return dict(all_boards=all_boards,
                header_links=header_links,
                site_config=site_config,
                footer_pages=footer_pages,
                extra_javascript=extra_javascript)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.static_folder, 'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/robots.txt')
def robots():
    return send_from_directory(app.static_folder, 'robots.txt')


@app.route('/manifest.json')
def manifest_json():
    manifest = configuration.app.manifest

    plugin_manager.execute_hook('manifest_json', manifest)

    return jsonify(manifest)


def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = ''.join(
            random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(32))
    return session['_csrf_token']


def generate_csrf_token_html():
    return Markup('<input name="token" type="hidden" value="{}">'.format(escape(generate_csrf_token())))


def with_token():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not check_csrf_token(request.form.get('token')):
                abort(400)

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def check_csrf_token(form_token):
    session_token = session.get('_csrf_token', None)
    return session_token is not None and form_token is not None and session_token == form_token


def check_csrf_referer(request):
    referer = request.headers.get('Referer', None)
    if not referer:
        return False

    parsed_url = urlparse(referer)

    return '{}://{}'.format(parsed_url.scheme, parsed_url.hostname) == configuration.app.site_url


def render_error(user_message, code=400, with_retry=False):
    if request.is_xhr:
        xhr_response = {
            'error': True
        }

        if user_message:
            xhr_response['message'] = page_formatting(user_message)

        return jsonify(xhr_response), code
    else:
        return render_template('error.html', message=user_message, with_retry=with_retry), code


app.jinja_env.globals['csrf_token'] = generate_csrf_token
app.jinja_env.globals['csrf_html'] = generate_csrf_token_html

import uchan.view.index
import uchan.view.thread
import uchan.view.post
import uchan.view.banned
import uchan.view.page
import uchan.view.verify
