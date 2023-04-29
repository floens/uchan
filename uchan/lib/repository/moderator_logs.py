from typing import List

from sqlalchemy import desc
from sqlalchemy.orm import joinedload

from uchan.lib.database import session
from uchan.lib.model import BoardModel, ModeratorLogModel
from uchan.lib.ormmodel import ModeratorLogOrmModel


def create(log: ModeratorLogModel):
    with session() as s:
        orm_model = log.to_orm_model()
        s.add(orm_model)
        s.commit()


def get_all_logs_by_board(
    board: BoardModel, offset: int, limit: int
) -> "List[ModeratorLogModel]":
    with session() as s:
        ls = (
            s.query(ModeratorLogOrmModel)
            .filter_by(board_id=board.id)
            .order_by(desc(ModeratorLogOrmModel.date))
            .options(joinedload(ModeratorLogOrmModel.moderator))
            .offset(offset)
            .limit(limit)
            .all()
        )

        res = list(
            map(lambda i: ModeratorLogModel.from_orm_model(i, with_moderator=True), ls)
        )
        s.commit()
        return res
