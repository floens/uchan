from typing import List

from sqlalchemy import desc
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.expression import cast
from sqlalchemy.sql.sqltypes import String

from uchan.lib import roles, action_authorizer
from uchan.lib.exceptions import ArgumentError
from uchan.lib.action_authorizer import ReportAction, PostAction
from uchan.lib.database import get_db
from uchan.lib.ormmodel import ReportOrmModel, BoardModeratorOrmModel, ThreadOrmModel, BoardOrmModel, PostOrmModel
from uchan.lib.model import ModeratorLogType, BoardModel, ModeratorModel
from uchan.lib.repository import reports
from uchan.lib.service import posts_service, moderator_service
from uchan.lib.tasks.report_task import ManageReportDetails
from uchan.lib.utils import now


def handle_manage_report(manage_report_details):
    report = find_report_id(manage_report_details.report_id)
    if not report:
        raise ArgumentError('Report not found')

    moderator = moderator_service.find_moderator_id(manage_report_details.mod_id)
    if not moderator:
        raise ArgumentError('Moderator not found')

    report_id = report.id
    post = report.post
    post_id = post.id
    board = post.thread.board

    if manage_report_details.mode == ManageReportDetails.CLEAR:
        action_authorizer.authorize_report_action(moderator, board, report, ReportAction.REPORT_CLEAR)
        delete_report(report)
        moderator_service.log(ModeratorLogType.REPORT_CLEAR, moderator, board,
                              'Cleared report id {}'.format(report_id))
    elif manage_report_details.mode == ManageReportDetails.DELETE_POST:
        action_authorizer.authorize_post_action(moderator, PostAction.POST_DELETE, post)
        # Report gets deleted with a cascade
        posts_service.delete_post(post)
        moderator_service.log(ModeratorLogType.REPORT_POST_DELETE, moderator, board,
                              'Post id {}'.format(post_id))
    elif manage_report_details.mode == ManageReportDetails.DELETE_FILE:
        action_authorizer.authorize_post_action(moderator, PostAction.POST_DELETE_FILE, post)
        posts_service.delete_file(post)
        moderator_service.log(ModeratorLogType.REPORT_POST_DELETE_FILE, moderator, board,
                              'Post id {}'.format(post_id))


def add_report(report):
    db = get_db()

    existing_report = None
    try:
        existing_report = db.query(ReportOrmModel).filter_by(post_id=report.post_id).one()
    except NoResultFound:
        pass

    if existing_report is not None:
        existing_report.count = ReportOrmModel.count + 1
    else:
        report.count = 1
        db.add(report)

    report.date = now()

    db.commit()


def delete_report(report):
    db = get_db()
    db.delete(report)
    db.commit()


def get_reports(moderator: ModeratorModel, page: int, per_page: int, for_boards: List[BoardModel] = None):
    return reports.get_reports(moderator, page, per_page, for_boards)


def find_report_id(id):
    db = get_db()
    try:
        return db.query(ReportOrmModel).filter_by(id=id).one()
    except NoResultFound:
        return None
