import logging
import random
import string
from functools import wraps
from urllib.parse import urlparse

from flask import (
    abort,
    jsonify,
    make_response,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from markupsafe import Markup, escape

from uchan import app, config
from uchan.filter.app_filters import page_formatting
from uchan.lib import plugin_manager
from uchan.lib.service import board_service, page_service, site_service
from uchan.lib.utils import ip4_to_str, now

logger = logging.getLogger(__name__)


class ExtraJavascript:
    def __init__(self):
        self.js = ""

    def add(self, js):
        self.js += js

    def gather(self):
        return self.js


@app.context_processor
def inject_variables():
    site_config = site_service.get_site_config()

    all_board_names = (
        board_service.get_all_board_names() if site_config.boards_top else None
    )

    footer_pages = page_service.find_footer_pages()

    extra_javascript = ExtraJavascript()
    plugin_manager.execute_hook("extra_javascript", extra_javascript)

    header_links = [
        ("mod", url_for("mod.mod_auth")),
    ]

    return dict(
        all_board_names=all_board_names,
        header_links=header_links,
        site_config=site_config,
        footer_pages=footer_pages,
        extra_javascript=extra_javascript,
    )


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        "view/static", "favicon.ico", mimetype="image/vnd.microsoft.icon"
    )


@app.route("/robots.txt")
def robots():
    return send_from_directory("view/static", "robots.txt")


@app.route("/manifest.json")
def manifest_json():
    manifest = config.manifest

    plugin_manager.execute_hook("manifest_json", manifest)

    return jsonify(manifest)


@app.route("/static/<path:path>")
def send_static_file(path):
    return send_from_directory("../" + config.asset_build_directory, path)


@app.route("/media/<path:path>")
def send_media_file(path):
    return send_from_directory("../" + config.local_cdn_path, path)


def generate_csrf_token():
    if "_csrf_token" not in session:
        session["_csrf_token"] = "".join(
            random.SystemRandom().choice(string.ascii_letters + string.digits)
            for _ in range(32)
        )
    return session["_csrf_token"]


def generate_csrf_token_html():
    return Markup(
        '<input name="token" type="hidden" value="{}">'.format(
            escape(generate_csrf_token())
        )
    )


def with_token():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not check_csrf_token(request.form.get("token")):
                abort(400)

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def with_cache_control_no_store():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = make_response(f(*args, **kwargs))
            response.headers.set("Cache-Control", "no-store")
            return response

        return decorated_function

    return decorator


def check_csrf_token(form_token):
    session_token = session.get("_csrf_token", None)
    return (
        session_token is not None
        and form_token is not None
        and session_token == form_token
    )


def check_csrf_referer(request):
    referer = request.headers.get("Referer", None)
    if not referer:
        return False

    parsed_url = urlparse(referer)

    final_url = "{}://{}".format(parsed_url.scheme, parsed_url.netloc)

    valid = final_url == config.site_url
    if not valid:
        logger.warn(
            'Referer not valid: "{}" is different than the configured url "{}"'.format(
                final_url, config.site_url
            )
        )

    return valid


def render_error(user_message, code=400, with_retry=False):
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        xhr_response = {"error": True}

        if user_message:
            xhr_response["message"] = page_formatting(user_message)

        return jsonify(xhr_response), code
    else:
        return (
            render_template("error.html", message=user_message, with_retry=with_retry),
            code,
        )


app.jinja_env.globals["csrf_token"] = generate_csrf_token
app.jinja_env.globals["csrf_html"] = generate_csrf_token_html
app.jinja_env.globals["ip4_to_str"] = ip4_to_str
app.jinja_env.globals["now"] = now

import uchan.view.index  # noqa
import uchan.view.thread  # noqa
import uchan.view.post  # noqa
import uchan.view.banned  # noqa
import uchan.view.page  # noqa
import uchan.view.verify  # noqa
import uchan.view.boards  # noqa
