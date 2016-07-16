from flask import render_template, request, abort, flash, redirect, url_for
from uchan import g
from uchan.filter.text_parser import parse_text
from uchan.lib import roles, ArgumentError, BadRequestError
from uchan.lib.cache.posts_cache import PostCacheProxy
from uchan.lib.database import get_db
from uchan.lib.models import Board
from uchan.lib.moderator_request import request_moderator
from uchan.lib.tasks.report_task import ManageReportDetails, manage_report_task
from uchan.lib.utils import ip4_to_str
from uchan.mod import mod
from uchan.view import with_token


@mod.route('/mod_report')
@mod.route('/mod_report/<int(max=14):page>')
@mod.route('/mod_report/<int(max=14):page>/<boards>')
def mod_report(page=0, boards=None):
    per_page = 20
    pages = 15

    moderator = request_moderator()
    is_admin = g.moderator_service.has_role(moderator, roles.ROLE_ADMIN)

    boards_set = None
    board_ids = []
    if boards is not None:
        query_set = set()

        for i in boards.split(','):
            if not g.board_service.check_board_name_validity(i):
                raise BadRequestError('Invalid boards')
            query_set.add(i)

        if len(query_set) > 6:
            raise BadRequestError('Maximum of 6 boards can be combined')

        db = get_db()
        query_boards = db.query(Board).filter(Board.name.in_(query_set)).all()
        if query_boards:
            boards_set = set()
            for board in query_boards:
                board_ids.append(board.id)
                boards_set.add(board.name)
        else:
            raise BadRequestError('Invalid boards')

    try:
        reports = g.report_service.get_reports(moderator, page, per_page, board_ids)
    except ArgumentError as e:
        raise BadRequestError(e)

    for report in reports:
        report.post_cache = PostCacheProxy(report.post, parse_text(report.post.text))

    view_ips = is_admin
    show_ban_button = is_admin

    moderator_boards = moderator.boards if not is_admin else g.board_service.get_all_boards()

    pager_suffix = '/' + ','.join(boards_set) if boards_set else ''
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
        report = g.report_service.find_report_id(report_id)
        if not report:
            abort(400)
        post_id = report.post_id
        return redirect(url_for('.mod_bans', post_id=post_id))

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
