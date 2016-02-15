from flask import render_template

from unichan import g
from unichan.lib import roles
from unichan.lib.moderator_request import get_authed_moderator
from unichan.mod import mod


@mod.route('/mod_post')
def mod_post():
    moderator = get_authed_moderator()
    reports = g.moderator_service.get_reports(moderator)

    view_ips = g.moderator_service.has_role(moderator, roles.ROLE_ADMIN)

    return render_template('mod_post.html', reports=reports, view_ips=view_ips, ip4_to_str=g.ban_service.ip4_to_str)
