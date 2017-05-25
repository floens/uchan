from typing import List

from uchan.lib import roles
from uchan.lib.database import session
from uchan.lib.exceptions import ArgumentError
from uchan.lib.model import ModeratorModel, BoardModel, BoardModeratorModel
from uchan.lib.ormmodel import BoardModeratorOrmModel, ModeratorOrmModel, BoardOrmModel

MESSAGE_BOARD_ALREADY_ADDED = 'Board already added to moderator'
MESSAGE_BOARD_NOT_ADDED = 'Moderator not on board'


def get_board_moderator(board: BoardModel, moderator: ModeratorModel) -> BoardModeratorModel:
    with session() as s:
        m = s.query(BoardModeratorOrmModel).filter_by(moderator_id=moderator.id, board_id=board.id).one_or_none()
        res = None
        if m:
            res = BoardModeratorModel.from_orm_model(m)
        s.commit()
        return res


def get_all_board_moderators_by_moderator(moderator: ModeratorModel) -> 'List[BoardModeratorModel]':
    with session() as s:
        bms = s.query(BoardModeratorOrmModel).filter_by(moderator_id=moderator.id).all()
        res = list(map(lambda i: BoardModeratorModel.from_orm_model(i), bms))
        s.commit()
        return res


def get_all_board_moderators_by_board(board: BoardModel) -> 'List[BoardModeratorModel]':
    with session() as s:
        bms = s.query(BoardModeratorOrmModel).filter_by(board_id=board.id).all()
        res = list(map(lambda i: BoardModeratorModel.from_orm_model(i), bms))
        s.commit()
        return res


def get_all_moderating_boards(moderator: ModeratorModel) -> 'List[BoardModel]':
    with session() as s:
        m = s.query(ModeratorOrmModel).filter_by(id=moderator.id).one()
        boards = list(map(lambda m: BoardModel.from_orm_model(m), m.boards))
        s.commit()
        return boards


def board_add_moderator(board: BoardModel, moderator: ModeratorModel):
    with session() as s:
        bm = s.query(BoardModeratorOrmModel).filter_by(moderator_id=moderator.id, board_id=board.id).one_or_none()
        if bm:
            raise ArgumentError(MESSAGE_BOARD_ALREADY_ADDED)
        m = s.query(ModeratorOrmModel).filter_by(id=moderator.id).one()
        b = s.query(BoardOrmModel).filter_by(id=board.id).one()
        b.moderators.append(m)
        s.commit()


def board_remove_moderator(board: BoardModel, moderator: ModeratorModel):
    with session() as s:
        bm = s.query(BoardModeratorOrmModel).filter_by(board_id=board.id, moderator_id=moderator.id).one_or_none()
        if not bm:
            raise ArgumentError(MESSAGE_BOARD_NOT_ADDED)
        s.delete(bm)
        s.commit()


def moderator_has_board(moderator: ModeratorModel, board: BoardModel) -> bool:
    with session() as s:
        m = s.query(BoardModeratorOrmModel).filter_by(moderator_id=moderator.id, board_id=board.id).one_or_none()
        res = m is not None
        s.commit()
        return res


def moderator_has_board_id(moderator: ModeratorModel, board_id: int) -> bool:
    with session() as s:
        m = s.query(BoardModeratorOrmModel).filter_by(moderator_id=moderator.id, board_id=board_id).one_or_none()
        res = m is not None
        s.commit()
        return res


# TODO: optimise
def has_any_of_board_roles(moderator: ModeratorModel, board: BoardModel, role_list: 'List[str]') -> bool:
    _check_board_roles(role_list)

    with session() as s:
        board_moderator = s.query(BoardModeratorOrmModel).filter_by(moderator_id=moderator.id, board_id=board.id).one()
        res = any(role in board_moderator.roles for role in role_list)
        s.commit()
        return res


def add_board_role(moderator: ModeratorModel, board: BoardModel, role: str):
    _check_board_roles([role])

    with session() as s:
        board_moderator = s.query(BoardModeratorOrmModel).filter_by(moderator_id=moderator.id, board_id=board.id).one()
        if role in board_moderator.roles:
            raise ArgumentError('Role already added')
        board_moderator.roles.append(role)
        s.commit()


def remove_board_role(moderator: ModeratorModel, board: BoardModel, role: str):
    _check_board_roles([role])

    with session() as s:
        board_moderator = s.query(BoardModeratorOrmModel).filter_by(moderator_id=moderator.id, board_id=board.id).one()
        if role not in board_moderator.roles:
            raise ArgumentError('Role not added')
        board_moderator.roles.remove(role)
        s.commit()


def _check_board_roles(role_list: 'List[str]'):
    if not all(role is not None and role in roles.ALL_BOARD_ROLES for role in role_list):
        raise ArgumentError('Invalid board role')
