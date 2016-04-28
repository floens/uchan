from flask import render_template, request
from uchan import g
from uchan.filter.text_parser import parse_text
from uchan.lib import roles
from uchan.lib.cache.posts_cache import PostCacheProxy
from uchan.lib.moderator_request import get_authed_moderator
from uchan.lib.utils import ip4_to_str
from uchan.mod import mod


@mod.route('/mod_post')
def mod_post():
    moderator = get_authed_moderator()
    reports = g.moderator_service.get_reports(moderator)

    for report in reports:
        report.post_cache = PostCacheProxy(report.post, parse_text(report.post.text))

    view_ips = g.moderator_service.has_role(moderator, roles.ROLE_ADMIN)

    return render_template('mod_post.html', reports=reports, view_ips=view_ips, ip4_to_str=ip4_to_str)


@mod.route('/mod_post/manage', methods=['POST'])
def mod_post_manage():
    form = request.form

    mode = form['mode']

    return 'mode: {}'.format(mode)
