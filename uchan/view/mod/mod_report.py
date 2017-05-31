from flask import render_template, request, abort, flash, redirect, url_for

from uchan.lib import roles
from uchan.lib.exceptions import BadRequestError, ArgumentError
from uchan.lib.moderator_request import request_moderator
from uchan.lib.service import board_service, moderator_service, report_service
from uchan.lib.tasks.report_task import ManageReportDetails, execute_manage_report_task
from uchan.lib.utils import ip4_to_str
from uchan.view import with_token
from uchan.view.mod import mod


@mod.route('/mod_report')
@mod.route('/mod_report/<int(max=14):page>')
@mod.route('/mod_report/<int(max=14):page>/<boards>')
def mod_report(page=0, boards=None):
    per_page = 20
    pages = 15

    moderator = request_moderator()
    is_admin = moderator_service.has_role(moderator, roles.ROLE_ADMIN)

    board_names = None
    if boards is not None:
        board_names = list(set(boards.split(',')))

        if len(board_names) > 6:
            raise BadRequestError('Maximum of 6 boards can be combined')

    try:
        if board_names:
            for_boards = board_service.find_by_names(list(board_names))
        else:
            for_boards = None

        reports = report_service.get_reports(moderator, page, per_page, for_boards)
    except ArgumentError as e:
        raise BadRequestError(e)

    view_ips = is_admin
    show_ban_button = is_admin

    if is_admin:
        moderator_boards = board_service.get_all_boards()
    else:
        moderator_boards = moderator_service.get_all_moderating_boards(moderator)

    pager_suffix = '/' + ','.join(board_names) if board_names else ''
    return render_template('mod_report.html', page=page, pages=pages, pager_suffix=pager_suffix,
                           moderator=moderator, reports=reports, moderator_boards=moderator_boards,
                           view_ips=view_ips, ip4_to_str=ip4_to_str, show_ban_button=show_ban_button)


@mod.route('/mod_report/manage', methods=['POST'])
@with_token()
def mod_report_manage():
    if request.form['mode'] == 'ban':
        return _handle_ban()

    details, success_message = _gather_report_manage_params()

    try:
        execute_manage_report_task(details)
    except ArgumentError as e:
        raise BadRequestError(e.message)

    flash(success_message)
    return redirect(url_for('.mod_report'))


def _handle_ban():
    report = report_service.find_report_id(request.form.get('report_id', type=int))
    if not report:
        abort(404)
    return redirect(url_for('.mod_bans', for_post=report.post.id))


def _gather_report_manage_params():
    form = request.form

    report_id = form.get('report_id', type=int)
    moderator = request_moderator()

    success_message = None
    mode_string = form['mode']

    if mode_string == 'clear':
        mode = ManageReportDetails.CLEAR
        success_message = 'Cleared report'
    elif mode_string == 'delete':
        mode = ManageReportDetails.DELETE_POST
        success_message = 'Deleted post'
    elif mode_string == 'delete_file':
        mode = ManageReportDetails.DELETE_FILE
        success_message = 'Deleted file'
    else:
        abort(400)

    return ManageReportDetails(report_id, moderator.id, mode), success_message
