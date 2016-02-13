from flask import render_template

from unichan import g
from unichan.lib.moderator_request import get_authed_moderator
from unichan.mod import mod


@mod.route('/mod_post')
def mod_post():
    reports = g.moderator_service.get_reports(get_authed_moderator())

    return render_template('mod_post.html', reports=reports)
