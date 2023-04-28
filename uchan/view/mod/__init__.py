from functools import wraps

from flask import Blueprint, url_for, request

from uchan.lib import roles
from uchan.lib.action_authorizer import NoPermissionError
from uchan.lib.moderator_request import request_has_role, get_authed

mod = Blueprint('mod', __name__, url_prefix='/mod', template_folder='templates')


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
            ('boards', ['mod.mod_boards', 'mod.mod_board_log']),
            ('reports', ['mod.mod_report'])
        ]

        if request_has_role(roles.ROLE_ADMIN):
            mod_links += [
                ('bans', ['mod.mod_bans']),
                ('moderators', ['mod.mod_moderators']),
                ('pages', ['mod.mod_pages']),
                ('site', ['mod.mod_site']),
            ]

        mod_links += [
            ('account', ['mod.mod_self']),
            ('logout', ['mod.mod_auth'])
        ]

        with_current_and_url = []
        for mod_link in mod_links:
            current = any(i.startswith(request.endpoint) for i in mod_link[1])
            with_current_and_url.append((mod_link[0], url_for(mod_link[1][0]), current))

        return dict(
            mod_links=with_current_and_url,
            is_authed=True
        )
    else:
        return {}


import uchan.view.mod.mod_auth
import uchan.view.mod.mod_report
import uchan.view.mod.mod_self
import uchan.view.mod.mod_board
import uchan.view.mod.mod_moderator
import uchan.view.mod.mod_site
import uchan.view.mod.mod_bans
import uchan.view.mod.mod_page
