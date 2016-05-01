from sqlalchemy import desc
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound

from uchan import g
from uchan.lib import roles, ArgumentError
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
        if not g.moderator_service.moderates_board(moderator, post.thread.board):
            raise ArgumentError('No permission')

        if manage_report_details.mode == ManageReportDetails.CLEAR:
            self.delete_report(report)
        elif manage_report_details.mode == ManageReportDetails.DELETE_POST:
            # Report gets deleted with a cascade
            g.posts_service.delete_post(post)
        elif manage_report_details.mode == ManageReportDetails.DELETE_FILE:
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

    def get_reports(self, moderator):
        db = get_db()

        reports_query = db.query(Report)
        # Show all reports when the moderator has the admin role
        if not g.moderator_service.has_role(moderator, roles.ROLE_ADMIN):
            # Filter that gets all reports for the moderator id
            reports_query = reports_query.filter(Report.post_id == Post.id, Post.thread_id == Thread.id,
                                                 Thread.board_id == Board.id,
                                                 Board.id == BoardModerator.board_id,
                                                 BoardModerator.moderator_id == moderator.id)

        reports_query = reports_query.order_by(desc(Report.date))
        reports_query = reports_query.options(
            joinedload('post').joinedload('thread').joinedload('board')
        )
        reports = reports_query.all()

        return reports

    def find_report_id(self, id):
        db = get_db()
        try:
            return db.query(Report).filter_by(id=id).one()
        except NoResultFound:
            return None
