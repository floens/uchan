from flask import render_template, request, abort, flash, redirect, url_for
from uchan import g
from uchan.filter.text_parser import parse_text
from uchan.lib import roles, ArgumentError, BadRequestError
from uchan.lib.cache.posts_cache import PostCacheProxy
from uchan.lib.moderator_request import request_moderator
from uchan.lib.tasks.report_task import ManageReportDetails, manage_report_task
from uchan.lib.utils import ip4_to_str
from uchan.mod import mod
from uchan.view import with_token


@mod.route('/mod_report')
def mod_report():
    moderator = request_moderator()
    reports = g.report_service.get_reports(moderator)

    for report in reports:
        report.post_cache = PostCacheProxy(report.post, parse_text(report.post.text))

    view_ips = g.moderator_service.has_role(moderator, roles.ROLE_ADMIN)

    board_links = []
    for board in g.moderator_service.get_moderating_boards(moderator):
        board_links.append((board.name, url_for('board', board_name=board.name)))

    return render_template('mod_report.html', moderator=moderator, reports=reports, board_links=board_links,
                           view_ips=view_ips, ip4_to_str=ip4_to_str)


@mod.route('/mod_report/manage', methods=['POST'])
@with_token()
def mod_report_manage():
    form = request.form

    report_id = form.get('report_id', type=int)
    moderator = request_moderator()
    details = ManageReportDetails(report_id, moderator.id)

    success_message = None
    mode_string = form['mode']
    if mode_string == 'clear':
        details.mode = ManageReportDetails.CLEAR
        success_message = 'Cleared report'
    elif mode_string == 'delete':
        details.mode = ManageReportDetails.DELETE_POST
        success_message = 'Deleted post'
    elif mode_string == 'delete_file':
        details.mode = ManageReportDetails.DELETE_FILE
        success_message = 'Deleted file'
    else:
        abort(400)

    try:
        manage_report_task.delay(details).get()
    except ArgumentError as e:
        raise BadRequestError(e.message)

    flash(success_message)
    return redirect(url_for('.mod_report'))
