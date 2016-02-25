import string

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import lazyload
from sqlalchemy.orm.exc import NoResultFound
from uchan import g
from uchan.lib import ArgumentError
from uchan.lib.configs import BoardConfig
from uchan.lib.database import get_db
from uchan.lib.models import Board


class BoardService:
    BOARD_NAME_MAX_LENGTH = 20
    BOARD_NAME_ALLOWED_CHARS = string.ascii_lowercase + string.digits + '_'

    DISALLOWED_BOARD_NAMES = [
        # Names that are routes now
        'mod', 'post_manage', 'banned', 'post', 'api', 'find_post', 'static', 'page',
        # names that can be confusing
        'admin', 'ban', 'bans', 'id', 'moderate', 'auth', 'login', 'logout', 'res', 'thread', 'threads',
        'board', 'boards', 'report', 'reports', 'user', 'users', 'log', 'logs', 'search', 'config', 'debug', 'create',
        'delete', 'update', 'faq', 'index', 'read'
    ]

    def get_all_boards(self):
        db = get_db()
        return db.query(Board).order_by(Board.name).all()

    def find_board(self, board_name, include_threads=False):
        try:
            q = get_db().query(Board)
            if include_threads:
                q = q.options(lazyload('threads'))
            board = q.filter_by(name=board_name).one()

            return board
        except NoResultFound:
            return None

    def board_add_moderator(self, board, moderator):
        db = get_db()
        board.moderators.append(moderator)
        db.commit()

    def board_remove_moderator(self, board, moderator):
        db = get_db()
        board.moderators.remove(moderator)
        db.commit()

    def check_board_name_validity(self, name):
        if not 0 < len(name) <= self.BOARD_NAME_MAX_LENGTH:
            return False

        if not all(c in self.BOARD_NAME_ALLOWED_CHARS for c in name):
            return False

        if name in self.DISALLOWED_BOARD_NAMES:
            return False

        return True

    def add_board(self, board):
        if not self.check_board_name_validity(board.name):
            raise ArgumentError('Invalid board name')

        db = get_db()

        board_config = BoardConfig()
        board.config_id = g.config_service.save_config(board_config, None).id

        db.add(board)

        try:
            db.commit()
        except IntegrityError:
            raise ArgumentError('Duplicate board name')

        g.board_cache.invalidate_all_boards()

    def delete_board(self, board):
        g.posts_cache.invalidate_board(board.name)
        g.board_cache.invalidate_all_boards()

        db = get_db()
        db.delete(board)
        db.commit()

    def update_board_config(self, board):
        g.board_cache.invalidate_board_config(board.name)

        get_db().commit()
