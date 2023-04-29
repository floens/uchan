from functools import wraps

from flask import Blueprint, request, url_for

from uchan.lib import roles
from uchan.lib.action_authorizer import NoPermissionError
from uchan.lib.moderator_request import get_authed, request_has_role

mod = Blueprint("mod", __name__, url_prefix="/mod", template_folder="templates")


def mod_role_restrict(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request_has_role(role):
                raise NoPermissionError()

            return f(*args, **kwargs)

        return decorated_function

    return decorator


@mod.context_processor
def inject_variables():
    if get_authed():
        mod_links = [
            ("boards", ["mod.mod_boards", "mod.mod_board_log"]),
            ("reports", ["mod.mod_report"]),
        ]

        if request_has_role(roles.ROLE_ADMIN):
            mod_links += [
                ("bans", ["mod.mod_bans"]),
                ("moderators", ["mod.mod_moderators"]),
                ("pages", ["mod.mod_pages"]),
                ("site", ["mod.mod_site"]),
            ]

        mod_links += [("account", ["mod.mod_self"]), ("logout", ["mod.mod_auth"])]

        with_current_and_url = []
        for mod_link in mod_links:
            current = any(i.startswith(request.endpoint) for i in mod_link[1])
            with_current_and_url.append((mod_link[0], url_for(mod_link[1][0]), current))

        return dict(mod_links=with_current_and_url, is_authed=True)
    else:
        return {}


import uchan.view.mod.mod_auth  # noqa
import uchan.view.mod.mod_report  # noqa
import uchan.view.mod.mod_self  # noqa
import uchan.view.mod.mod_board  # noqa
import uchan.view.mod.mod_moderator  # noqa
import uchan.view.mod.mod_site  # noqa
import uchan.view.mod.mod_bans  # noqa
import uchan.view.mod.mod_page  # noqa
