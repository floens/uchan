import string

import bcrypt
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm.exc import NoResultFound

from uchan import g
from uchan.lib import ArgumentError
from uchan.lib import roles
from uchan.lib.database import get_db
from uchan.lib.mod_log import mod_log
from uchan.lib.models import Moderator
from uchan.lib.models.board import BoardModerator


class ModeratorService:
    USERNAME_MAX_LENGTH = 50
    USERNAME_ALLOWED_CHARS = string.ascii_letters + string.digits + '_'
    PASSWORD_MIN_LENGTH = 6
    PASSWORD_MAX_LENGTH = 50
    PASSWORD_ALLOWED_CHARS = string.ascii_letters + string.digits + string.punctuation + '_'

    BOARDS_PER_MODERATOR = 2

    def __init__(self):
        pass

    def get_moderating_boards(self, moderator):
        if self.has_role(moderator, roles.ROLE_ADMIN):
            return g.board_service.get_all_boards()

        boards = []
        for board_moderator in moderator.board_moderator:
            boards.append(board_moderator.board)
        return boards

    def moderates_board(self, moderator, board):
        if self.has_role(moderator, roles.ROLE_ADMIN):
            return True
        return board in moderator.boards

    def board_role_exists(self, role):
        return role is not None and role in roles.ALL_BOARD_ROLES

    def has_board_role(self, moderator, board, role):
        if self.has_role(moderator, roles.ROLE_ADMIN):
            return

        if board not in moderator.boards:
            raise ArgumentError('Not a moderator of that board')

        if not self.board_role_exists(role):
            raise ArgumentError('Invalid board role')

        board_moderator_roles = self.get_board_roles(moderator, board)
        return role in board_moderator_roles

    def get_board_roles(self, moderator, board):
        if board not in moderator.boards:
            raise ArgumentError('Not a moderator of that board')
        return []

        # db = get_db()
        # try:
        #     return db.query(board_moderator_table.c.roles).filter(
        #         board_moderator_table.c.moderator_id == moderator.id,
        #         board_moderator_table.c.board_id == board.id).one()[0]
        # except NoResultFound:
        #     raise ArgumentError('Not a moderator of that board')

    def add_board_role(self, moderator, board, role):
        if board not in moderator.boards:
            raise ArgumentError('Not a moderator of that board')

        if not self.board_role_exists(role):
            raise ArgumentError('Invalid board role')

        db = get_db()

        board_moderator = db.query(BoardModerator).filter_by(board_id=board.id, moderator_id=moderator.id).one()
        board_moderator.roles.append(role)
        db.commit()

    def remove_board_role(self, moderator, board, role):
        if board not in moderator.boards:
            raise ArgumentError('Not a moderator of that board')

        if not self.board_role_exists(role):
            raise ArgumentError('Invalid board role')

        board_moderator_roles = self.get_board_roles(moderator, board)

        if not role not in board_moderator_roles:
            raise ArgumentError('Role not on moderator')

            # board_moderator_roles.remove(role)
            # db = get_db()
            # db.execute(update(board_moderator_table)
            #            .where(board_moderator_table.c.moderator_id == moderator.id)
            #            .where(board_moderator_table.c.board_id == board.id)
            #            .values(roles=board_moderator_roles))

    def user_create_board(self, moderator, board):
        db = get_db()

        is_admin = self.has_role(moderator, roles.ROLE_ADMIN)

        if not is_admin:
            # Queries the boardmoderator linking table for how many
            # boards this moderator is the creator of
            result = db.execute('SELECT count(*) AS rolecount FROM boardmoderator bm '
                                'WHERE bm.moderator_id = :moderator_id AND '
                                'bm.roles @> ARRAY[:role]::VARCHAR[];', {
                                    'moderator_id': moderator.id,
                                    'role': roles.BOARD_ROLE_CREATOR
                                })

            count = result.fetchone()[0]

            if count >= self.BOARDS_PER_MODERATOR:
                raise ArgumentError('You cannot create a new board')

        g.board_service.add_board(board)
        g.board_service.board_add_moderator(board, moderator)
        self.add_board_role(moderator, board, roles.BOARD_ROLE_CREATOR)

        return board

    def user_register(self, username, password, password_repeat):
        if not self.check_username_validity(username):
            raise ArgumentError('Invalid username')

        if not self.check_password_validity(password) or not self.check_password_validity(password_repeat):
            raise ArgumentError('Invalid password')

        if password != password_repeat:
            raise ArgumentError('Password does not match')

        if self.find_moderator_username(username) is not None:
            raise ArgumentError('Username taken')

        moderator = Moderator()
        moderator.roles = []
        moderator.username = username

        self.create_moderator(moderator, password)

        mod_log('User {} registered'.format(username))

        return moderator

    def check_username_validity(self, username):
        if not 0 < len(username) <= self.USERNAME_MAX_LENGTH:
            return False

        if not all(c in self.USERNAME_ALLOWED_CHARS for c in username):
            return False

        return True

    def check_password_validity(self, password):
        if password is None or len(password) < self.PASSWORD_MIN_LENGTH or len(password) >= self.PASSWORD_MAX_LENGTH:
            return False

        if not all(c in self.PASSWORD_ALLOWED_CHARS for c in password):
            return False

        return True

    def create_moderator(self, moderator, password):
        if not self.check_username_validity(moderator.username):
            raise ArgumentError('Invalid username')

        if not self.check_password_validity(password):
            raise ArgumentError('Invalid password')

        moderator.password = self.hash_password(password)

        db = get_db()
        db.add(moderator)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ArgumentError('Duplicate username')

    def delete_moderator(self, moderator):
        db = get_db()
        db.delete(moderator)
        db.commit()

    def find_moderator_id(self, id):
        db = get_db()
        try:
            return db.query(Moderator).filter_by(id=id).one()
        except NoResultFound:
            return None

    def find_moderator_username(self, username):
        db = get_db()
        try:
            return db.query(Moderator).filter_by(username=username).one()
        except NoResultFound:
            return None

    def get_all_moderators(self):
        return get_db().query(Moderator).all()

    def role_exists(self, role):
        return role is not None and role in roles.ALL_ROLES

    def has_role(self, moderator, role):
        return role is not None and role in moderator.roles

    def add_role(self, moderator, role):
        if not self.role_exists(role):
            raise ArgumentError('Invalid role')

        if self.has_role(moderator, role):
            raise ArgumentError('Role already added')

        moderator.roles.append(role)

        db = get_db()
        db.commit()

    def remove_role(self, moderator, role):
        if not role:
            raise ArgumentError('Invalid role')

        if not self.has_role(moderator, role):
            raise ArgumentError('Role not on moderator')

        moderator.roles.remove(role)

        db = get_db()
        db.commit()

    def change_password(self, moderator, old_password, new_password):
        if not self.check_password_validity(old_password):
            raise ArgumentError('Invalid password')

        self.check_password(moderator, old_password)

        self._update_password(moderator, new_password)

    def change_password_admin(self, moderator, new_password):
        self._update_password(moderator, new_password)

    def check_password(self, moderator, password):
        moderator_hashed_password = moderator.password

        if bcrypt.hashpw(password.encode(), moderator_hashed_password) != moderator_hashed_password:
            raise ArgumentError('Password does not match')

    def hash_password(self, password):
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    def _update_password(self, moderator, new_password):
        if not self.check_password_validity(new_password):
            raise ArgumentError('Invalid new password')

        moderator.password = self.hash_password(new_password)

        db = get_db()
        db.commit()
