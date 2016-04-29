from flask import render_template, request, abort, flash, redirect, url_for
from uchan import g
from uchan.filter.text_parser import parse_text
from uchan.lib import roles, ArgumentError, BadRequestError
from uchan.lib.cache.posts_cache import PostCacheProxy
from uchan.lib.moderator_request import get_authed_moderator
from uchan.lib.tasks.report_task import ManageReportDetails, manage_report_task
from uchan.lib.utils import ip4_to_str
from uchan.mod import mod
from uchan.view import with_token


@mod.route('/mod_post')
def mod_post():
    moderator = get_authed_moderator()
    reports = g.report_service.get_reports(moderator)

    for report in reports:
        report.post_cache = PostCacheProxy(report.post, parse_text(report.post.text))

    view_ips = g.moderator_service.has_role(moderator, roles.ROLE_ADMIN)

    board_links = []
    for board in moderator.boards:
        board_links.append((board.name, url_for('board', board_name=board.name)))

    x = g.report_service.has_report_role(moderator, moderator.boards[0], 'janitor')

    return render_template('mod_post.html', moderator=moderator, reports=reports, board_links=board_links,
                           view_ips=view_ips, ip4_to_str=ip4_to_str, x=x)


@mod.route('/mod_post/manage', methods=['POST'])
@with_token()
def mod_post_manage():
    form = request.form

    report_id = form.get('report_id', type=int)
    moderator = get_authed_moderator()
    details = ManageReportDetails(report_id, moderator.id)

    success_message = None
    mode_string = form['mode']
    if mode_string == 'clear':
        details.mode = ManageReportDetails.CLEAR
        success_message = 'Cleared report'
    elif mode_string == 'delete':
        details.mode = ManageReportDetails.DELETE_POST
        success_message = 'Deleted post'
    else:
        abort(400)

    try:
        manage_report_task.delay(details).get()
    except ArgumentError as e:
        raise BadRequestError(e.message)

    flash(success_message)
    return redirect(url_for('.mod_post'))
