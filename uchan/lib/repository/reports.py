from typing import List, Optional

from sqlalchemy import cast, desc
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.sqltypes import String

from uchan.lib import roles
from uchan.lib.database import session
from uchan.lib.model import ModeratorModel, BoardModel, ReportModel, PostModel
from uchan.lib.ormmodel import PostOrmModel, ThreadOrmModel, BoardOrmModel, BoardModeratorOrmModel, ReportOrmModel
from uchan.lib.service.moderator_service import required_roles_for_viewing_reports, has_role


def create(report: ReportModel):
    with session() as s:
        m = report.to_orm_model()
        s.add(m)
        s.commit()
        r = ReportModel.from_orm_model(m)
        s.commit()
        return r


def find_by_id(report_id: int) -> Optional[ReportModel]:
    with session() as s:
        m = s.query(ReportOrmModel).filter_by(id=report_id).one()
        res = None
        if m:
            res = ReportModel.from_orm_model(m)
        s.commit()
        return res


def find_by_post(post: PostModel) -> Optional[ReportModel]:
    with session() as s:
        m = s.query(ReportOrmModel).filter_by(post_id=post.id).one_or_none()
        res = None
        if m:
            res = ReportModel.from_orm_model(m)
        s.commit()
        return res


def find_by_moderator(moderator: ModeratorModel, page: int, per_page: int, for_boards: List[BoardModel]) \
        -> List[ReportModel]:
    with session() as s:
        q = s.query(ReportOrmModel)

        can_see_all_reports = has_role(moderator, roles.ROLE_ADMIN)

        if not can_see_all_reports:
            # Filter that gets all reports for the moderator id, if that moderator also has either
            # full permission or janitor.
            q = q.filter(
                ReportOrmModel.post_id == PostOrmModel.id,
                PostOrmModel.thread_id == ThreadOrmModel.id,
                ThreadOrmModel.board_id == BoardOrmModel.id,
                BoardOrmModel.id == BoardModeratorOrmModel.board_id,
                BoardModeratorOrmModel.moderator_id == moderator.id,
                BoardModeratorOrmModel.roles.overlap(cast(required_roles_for_viewing_reports(), ARRAY(String))))
        else:
            q = q.filter(
                ReportOrmModel.post_id == PostOrmModel.id,
                PostOrmModel.thread_id == ThreadOrmModel.id,
                ThreadOrmModel.board_id == BoardOrmModel.id)

        if for_boards:
            board_ids = [board.id for board in for_boards]
            q = q.filter(BoardOrmModel.id.in_(board_ids))

        q = q.order_by(desc(ReportOrmModel.date))
        q = q.options(
            joinedload('post').joinedload('thread').joinedload('board')
        )
        q = q.offset(page * per_page).limit(per_page)

        res = list(map(lambda i: ReportModel.from_orm_model(i), q.all()))
        s.commit()
        return res


def increase_report_count(report: ReportModel):
    with session() as s:
        m = s.query(ReportOrmModel).filter_by(id=report.id).one()
        m.count = ReportOrmModel.count + 1
        s.commit()


def delete(report: ReportModel):
    with session() as s:
        m = s.query(ReportOrmModel).filter_by(id=report.id).one()
        s.delete(m)
        s.commit()
