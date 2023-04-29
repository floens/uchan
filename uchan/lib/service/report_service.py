from typing import List, Optional

from uchan.lib import action_authorizer
from uchan.lib.action_authorizer import PostAction, ReportAction
from uchan.lib.exceptions import ArgumentError
from uchan.lib.model import (
    BoardModel,
    ModeratorLogType,
    ModeratorModel,
    PostModel,
    ReportModel,
)
from uchan.lib.repository import reports
from uchan.lib.service import moderator_service, posts_service
from uchan.lib.tasks.report_task import ManageReportDetails
from uchan.lib.utils import now

MESSAGE_REPORT_NOT_FOUND = "Report not found"
MESSAGE_MODERATOR_NOT_FOUND = "Moderator not found"


def handle_manage_report(manage_report_details):
    report = reports.find_by_id(manage_report_details.report_id)
    if not report:
        raise ArgumentError(MESSAGE_REPORT_NOT_FOUND)

    moderator = moderator_service.find_moderator_id(manage_report_details.mod_id)
    if not moderator:
        raise ArgumentError(MESSAGE_MODERATOR_NOT_FOUND)

    post = report.post
    board = post.thread.board

    if manage_report_details.mode == ManageReportDetails.CLEAR:
        action_authorizer.authorize_report_action(
            moderator, board, report, ReportAction.REPORT_CLEAR
        )
        delete_report(report)

        message = "Cleared report id {}".format(report.id)
        moderator_service.log(ModeratorLogType.REPORT_CLEAR, moderator, board, message)
    elif manage_report_details.mode == ManageReportDetails.DELETE_POST:
        action_authorizer.authorize_post_action(moderator, PostAction.POST_DELETE, post)
        # Report gets deleted with a cascade
        posts_service.delete_post(post)

        message = "Post id {}".format(post.id)
        moderator_service.log(
            ModeratorLogType.REPORT_POST_DELETE, moderator, board, message
        )
    elif manage_report_details.mode == ManageReportDetails.DELETE_FILE:
        action_authorizer.authorize_post_action(
            moderator, PostAction.POST_DELETE_FILE, post
        )
        posts_service.delete_file(post)

        message = "Post id {}".format(post.id)
        moderator_service.log(
            ModeratorLogType.REPORT_POST_DELETE_FILE, moderator, board, message
        )


def report_post(post: PostModel):
    existing_report = reports.find_by_post(post)
    if existing_report:
        reports.increase_report_count(existing_report)
    else:
        report = ReportModel.from_post_count_date(post, 1, now())
        reports.create(report)


def delete_report(report: ReportModel):
    reports.delete(report)


def get_reports(
    moderator: ModeratorModel,
    page: int,
    per_page: int,
    for_boards: List[BoardModel] = None,
):
    return reports.find_by_moderator(moderator, page, per_page, for_boards)


def find_report_id(report_id: int) -> Optional[ReportModel]:
    return reports.find_by_id(report_id)
