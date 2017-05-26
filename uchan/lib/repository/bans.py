from typing import Optional, List

from sqlalchemy import desc

from uchan.lib.database import session
from uchan.lib.model import BanModel, BoardModel
from uchan.lib.ormmodel import BanOrmModel


# TODO: avoid duplicates
def create_ban(ban: BanModel) -> BanModel:
    with session() as s:
        eq = s.query(BanOrmModel)

        m = ban.to_orm_model()
        s.add(m)
        s.commit()
        return BanModel.from_orm_model(m)


def count():
    with session() as s:
        r = s.query(BanOrmModel).count()
        s.commit()
        return r


def get_all(offset: int, limit: int):
    with session() as s:
        q = s.query(BanOrmModel).order_by(desc(BanOrmModel.date)).limit(limit).offset(offset)
        r = list(map(lambda i: BanModel.from_orm_model(i), q.all()))
        s.commit()
        return r


def find_by_id(ban_id: int) -> Optional[BanModel]:
    with session() as s:
        m = s.query(BanOrmModel).filter_by(id=ban_id).one_or_none()
        res = None
        if m:
            res = BanModel.from_orm_model(m)
        s.commit()
        return res


def find_by_ip4(ip4: int, for_board: BoardModel = None) -> List[BanModel]:
    with session() as s:
        q = s.query(BanOrmModel)
        q = q.filter((BanOrmModel.ip4 == ip4) | ((BanOrmModel.ip4 <= ip4) & (BanOrmModel.ip4_end >= ip4)))

        if for_board:
            q = q.filter((BanOrmModel.board == None) | (BanOrmModel.board == for_board.name))

        q = q.order_by(desc(BanOrmModel.date))

        res = list(map(lambda i: BanModel.from_orm_model(i), q.all()))
        s.commit()
        return res


def delete_ban(ban: BanModel):
    with session() as s:
        m = s.query(BanOrmModel).filter_by(id=ban.id).one()
        s.delete(m)
        s.commit()
