from sqlalchemy import desc
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.sqltypes import String
from sqlalchemy.sql.expression import cast

from uchan import g
from uchan.lib import roles, ArgumentError, NoPermissionError
from uchan.lib.action_authorizer import ReportAction, PostAction
from uchan.lib.database import get_db
from uchan.lib.models import Report, BoardModerator, Thread, Board, Post
from uchan.lib.tasks.report_task import ManageReportDetails
from uchan.lib.utils import now


class ReportService:
    def __init__(self):
        pass

    def handle_manage_report(self, manage_report_details):
        report = self.find_report_id(manage_report_details.report_id)
        if not report:
            raise ArgumentError('Report not found')

        moderator = g.moderator_service.find_moderator_id(manage_report_details.mod_id)
        if not moderator:
            raise ArgumentError('Moderator not found')

        post = report.post
        board = post.thread.board

        if manage_report_details.mode == ManageReportDetails.CLEAR:
            g.action_authorizer.authorize_report_action(moderator, board, report, ReportAction.REPORT_CLEAR)
            self.delete_report(report)
        elif manage_report_details.mode == ManageReportDetails.DELETE_POST:
            g.action_authorizer.authorize_post_action(moderator, PostAction.POST_DELETE, post)
            # Report gets deleted with a cascade
            g.posts_service.delete_post(post)
        elif manage_report_details.mode == ManageReportDetails.DELETE_FILE:
            g.action_authorizer.authorize_post_action(moderator, PostAction.POST_DELETE_FILE, post)
            g.posts_service.delete_file(post)

    def add_report(self, report):
        db = get_db()

        existing_report = None
        try:
            existing_report = db.query(Report).filter_by(post_id=report.post_id).one()
        except NoResultFound:
            pass

        if existing_report is not None:
            existing_report.count = Report.count + 1
        else:
            report.count = 1
            db.add(report)

        report.date = now()

        db.commit()

    def delete_report(self, report):
        db = get_db()
        db.delete(report)
        db.commit()

    def get_reports(self, moderator, page, per_page, board_ids=None):
        db = get_db()

        reports_query = db.query(Report)
        # Show all reports when the moderator has the admin role
        if not g.moderator_service.has_role(moderator, roles.ROLE_ADMIN):
            # Filter that gets all reports for the moderator id
            reports_query = reports_query.filter(Report.post_id == Post.id, Post.thread_id == Thread.id,
                                                 Thread.board_id == Board.id,
                                                 Board.id == BoardModerator.board_id,
                                                 BoardModerator.moderator_id == moderator.id,
                                                 BoardModerator.roles.contains(
                                                     cast([roles.BOARD_ROLE_JANITOR], ARRAY(String))))
        else:
            reports_query = reports_query.filter(Report.post_id == Post.id, Post.thread_id == Thread.id,
                                                 Thread.board_id == Board.id)

        if board_ids:
            reports_query = reports_query.filter(Board.id.in_(board_ids))

        reports_query = reports_query.order_by(desc(Report.date))
        reports_query = reports_query.options(
            joinedload('post').joinedload('thread').joinedload('board')
        )
        reports = reports_query.offset(page * per_page).limit(per_page).all()

        return reports

    def find_report_id(self, id):
        db = get_db()
        try:
            return db.query(Report).filter_by(id=id).one()
        except NoResultFound:
            return None
