from flask import Blueprint, url_for
from functools import wraps
from uchan.lib import roles
from uchan.lib.action_authorizer import NoPermissionError
from uchan.lib.moderator_request import request_has_role, get_authed

mod = Blueprint('mod', __name__, url_prefix='/mod', template_folder='templates', static_folder='static')


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
            ('auth', url_for('.mod_auth')),
            ('mod reports', url_for('.mod_report')),
            ('mod account', url_for('.mod_self')),
            ('mod boards', url_for('.mod_boards'))
        ]

        if request_has_role(roles.ROLE_ADMIN):
            mod_links += [
                ('mod bans', url_for('.mod_bans')),
                ('stats', url_for('.mod_stat')),
                ('memcache stats', url_for('.mod_memcache_stat')),
                ('mod moderators', url_for('.mod_moderators')),
                ('mod pages', url_for('.mod_pages')),
                ('mod site', url_for('.mod_site')),
            ]

        return dict(mod_links=mod_links)
    else:
        return {}


import uchan.mod.mod_auth
import uchan.mod.mod_report
import uchan.mod.mod_self
import uchan.mod.mod_board
import uchan.mod.mod_moderator
import uchan.mod.mod_site
import uchan.mod.mod_bans
import uchan.mod.mod_page
