from functools import wraps

from flask import Blueprint, request, url_for, redirect, render_template

from unichan.lib import roles
from unichan.lib.moderator_request import request_has_role, get_authed

mod = Blueprint('mod', __name__, url_prefix='/mod', template_folder='templates')


def mod_abort_redirect():
    return redirect(url_for('.mod_auth'))


@mod.before_request
def mod_restrict():
    if request.endpoint != 'mod.mod_auth' and not get_authed():
        return mod_abort_redirect()


def mod_role_restrict(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request_has_role(role):
                return render_template('error.html', message='No permission')

            return f(*args, **kwargs)

        return decorated_function

    return decorator


@mod.context_processor
def inject_variables():
    if get_authed():
        mod_links = [
            ('auth', url_for('.mod_auth')),
            ('mod posts', url_for('.mod_post'))
        ]

        if request_has_role(roles.ROLE_ADMIN):
            mod_links.append(('stats', url_for('.mod_stat')))
            mod_links.append(('memcache stats', url_for('.mod_memcache_stat')))
            mod_links.append(('mod moderators', url_for('.mod_moderators')))
            mod_links.append(('mod boards', url_for('.mod_boards')))
            mod_links.append(('mod site', url_for('.mod_site')))

        return dict(mod_links=mod_links)
    else:
        return {}


import unichan.mod.views
