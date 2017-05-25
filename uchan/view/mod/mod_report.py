from flask import render_template, request, abort, flash, redirect, url_for

from uchan.filter.text_parser import parse_text
from uchan.lib import roles, validation
from uchan.lib.exceptions import BadRequestError, ArgumentError
from uchan.lib.database import get_db
from uchan.lib.ormmodel import BoardOrmModel
from uchan.lib.moderator_request import request_moderator
from uchan.lib.service import board_service, moderator_service, report_service
from uchan.lib.tasks.report_task import ManageReportDetails, manage_report_task
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

    moderator_boards = moderator.boards if not is_admin else board_service.get_all_boards()

    pager_suffix = '/' + ','.join(board_names) if board_names else ''
    return render_template('mod_report.html', page=page, pages=pages, pager_suffix=pager_suffix,
                           moderator=moderator, reports=reports, moderator_boards=moderator_boards,
                           view_ips=view_ips, ip4_to_str=ip4_to_str, show_ban_button=show_ban_button)


@mod.route('/mod_report/manage', methods=['POST'])
@with_token()
def mod_report_manage():
    form = request.form

    report_id = form.get('report_id', type=int)
    moderator = request_moderator()
    details = ManageReportDetails(report_id, moderator.id)

    success_message = None
    mode_string = form['mode']
    if mode_string == 'ban':
        report = report_service.find_report_id(report_id)
        if not report:
            abort(400)
        post_id = report.post_id
        return redirect(url_for('.mod_bans', for_post=post_id))

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
