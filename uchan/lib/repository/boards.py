from typing import List, Optional

from uchan.lib import validation
from uchan.lib.cache import board_cache, cache, cache_key
from uchan.lib.configs import BoardConfig
from uchan.lib.database import session
from uchan.lib.exceptions import ArgumentError
from uchan.lib.model import BoardModel
from uchan.lib.ormmodel import BoardOrmModel
from uchan.lib.service import config_service

MESSAGE_DUPLICATE_BOARD_NAME = 'Duplicate board name'
MESSAGE_INVALID_NAME = 'Invalid board name'


def create(board: BoardModel) -> BoardModel:
    if not validation.check_board_name_validity(board.name):
        raise ArgumentError(MESSAGE_INVALID_NAME)

    with session() as s:
        existing = s.query(BoardOrmModel).filter_by(name=board.name).one_or_none()
        if existing:
            raise ArgumentError(MESSAGE_DUPLICATE_BOARD_NAME)

        orm_board = board.to_orm_model()

        # TODO clean this up
        board_config = BoardConfig()
        orm_board.config_id = config_service.save_config(board_config, None).id

        s.add(orm_board)
        s.commit()

        board = board.from_orm_model(orm_board)

        cache.set(cache_key('board_and_config', board.name), board.to_cache())
        board_cache.invalidate_all_boards()

        return board


def update_config(board: BoardModel):
    with session() as s:
        s.merge(board.config.to_orm_model())
        s.commit()
        cache.set(cache_key('board_and_config', board.name), board.to_cache())


def get_all() -> 'List[BoardModel]':
    with session() as s:
        b = s.query(BoardOrmModel).order_by(BoardOrmModel.name).all()
        res = list(map(lambda i: BoardModel.from_orm_model(i), b))
        s.commit()
        return res


# TODO: we always include the config, remove argument
def find_by_name(name: str, include_config=False) -> Optional[BoardModel]:
    if not validation.check_board_name_validity(name):
        raise ArgumentError(MESSAGE_INVALID_NAME)

    board_cache = cache.get(cache_key('board_and_config', name))
    if not board_cache:
        with session() as s:
            board_orm_model = s.query(BoardOrmModel).filter_by(name=name).one_or_none()
            if not board_orm_model:
                return None
            board = BoardModel.from_orm_model(board_orm_model, include_config=True)
            cache.set(cache_key('board_and_config', name), board.to_cache())
            return board

    return BoardModel.from_cache(board_cache)


# unknown names are ignored!
def find_by_names(names: List[str]) -> List[BoardModel]:
    for name in names:
        if not validation.check_board_name_validity(name):
            raise ArgumentError(MESSAGE_INVALID_NAME)

    boards = []
    with session() as s:
        for name in names:
            board_cache = cache.get(cache_key('board_and_config', name))
            if board_cache:
                boards.append(BoardModel.from_cache(board_cache))
            else:
                board_orm_model = s.query(BoardOrmModel).filter_by(name=name).one_or_none()
                if board_orm_model:
                    board = BoardModel.from_orm_model(board_orm_model, include_config=True)
                    cache.set(cache_key('board_and_config', name), board.to_cache())
                    boards.append(board)

    return boards


def delete(board: BoardModel):
    with session() as s:
        b = s.query(BoardOrmModel).filter_by(id=board.id).one()
        s.delete(b)
        s.commit()

        board_cache.invalidate_all_boards()
        board_cache.invalidate_board_config(board.name)
        # posts_cache.delete_board_cache(board.name)
