import string

BOARD_NAME_MAX_LENGTH = 20
BOARD_NAME_ALLOWED_CHARS = string.ascii_lowercase + string.digits + '_'

DISALLOWED_BOARD_NAMES = [
    # Names that are routes now
    'mod', 'post_manage', 'banned', 'post', 'api', 'find_post', 'static', 'page', 'verify',
    # names that can be confusing
    'admin', 'ban', 'bans', 'id', 'moderate', 'auth', 'login', 'logout', 'res', 'thread', 'threads',
    'board', 'boards', 'report', 'reports', 'user', 'users', 'log', 'logs', 'search', 'config', 'debug', 'create',
    'delete', 'update', 'faq', 'index', 'read', 'all'
]

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import lazyload
from sqlalchemy.orm.exc import NoResultFound
from uchan.lib import ArgumentError
from uchan.lib.cache import board_cache, posts_cache
from uchan.lib.configs import BoardConfig
from uchan.lib.database import get_db
from uchan.lib.models import Board, BoardModerator
from uchan.lib.service import config_service


def get_all_boards():
    db = get_db()
    return db.query(Board).order_by(Board.name).all()


def find_board(board_name, include_threads=False):
    try:
        q = get_db().query(Board)
        if include_threads:
            q = q.options(lazyload('threads'))
        board = q.filter_by(name=board_name).one()

        return board
    except NoResultFound:
        return None


def board_add_moderator(board, moderator):
    db = get_db()

    if board in moderator.boards:
        raise ArgumentError('Board already added to moderator')

    board.moderators.append(moderator)
    db.commit()


def board_remove_moderator(board, moderator):
    db = get_db()

    try:
        board_moderator = db.query(BoardModerator).filter_by(
            board_id=board.id,
            moderator_id=moderator.id
        ).one()
    except NoResultFound:
        raise ArgumentError('Moderator not on board')
    db.delete(board_moderator)
    db.commit()


def check_board_name_validity(name):
    if not 0 < len(name) <= BOARD_NAME_MAX_LENGTH:
        return False

    if not all(c in BOARD_NAME_ALLOWED_CHARS for c in name):
        return False

    if name in DISALLOWED_BOARD_NAMES:
        return False

    return True


def add_board(board):
    if not check_board_name_validity(board.name):
        raise ArgumentError('Invalid board name')

    db = get_db()

    board_config = BoardConfig()
    board.config_id = config_service.save_config(board_config, None).id

    db.add(board)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ArgumentError('Duplicate board name')

    board_cache.invalidate_all_boards()


def delete_board(board):
    db = get_db()
    db.delete(board)
    db.commit()

    board_cache.invalidate_all_boards()
    board_cache.invalidate_board_config(board.name)
    posts_cache.delete_board_cache(board.name)


def update_board_config(board):
    get_db().commit()

    board_cache.invalidate_board_config(board.name)
    posts_cache.invalidate_board(board.name)
