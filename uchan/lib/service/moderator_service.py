import string
from enum import Enum

import bcrypt
from flask import flash
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from uchan import g
from uchan.lib import ArgumentError, NoPermissionError
from uchan.lib import roles
from uchan.lib.database import get_db
from uchan.lib.mod_log import mod_log
from uchan.lib.models import Moderator
from uchan.lib.models.board import BoardModerator


class ModeratorAction(Enum):
    BOARD_CREATE = 1
    BOARD_DELETE = 2


class ModeratorBoardAction(Enum):
    MODERATOR_ADD = 1
    MODERATOR_REMOVE = 2
    MODERATOR_REMOVE_SELF = 3
    ROLES_UPDATE = 4
    ROLE_ADD = 5
    ROLE_REMOVE = 6
    CONFIG_UPDATE = 7


class ModeratorService:
    USERNAME_MAX_LENGTH = 50
    USERNAME_ALLOWED_CHARS = string.ascii_letters + string.digits + '_'
    PASSWORD_MIN_LENGTH = 6
    PASSWORD_MAX_LENGTH = 50
    PASSWORD_ALLOWED_CHARS = string.ascii_letters + string.digits + string.punctuation + '_'

    BOARDS_PER_MODERATOR = 2

    def __init__(self):
        pass

    def user_create_board(self, moderator, board):
        self.authorize_action(moderator, ModeratorAction.BOARD_CREATE)

        g.board_service.add_board(board)
        g.board_service.board_add_moderator(board, moderator)
        self.add_board_role(moderator, board, roles.BOARD_ROLE_CREATOR)

        return board

    def user_delete_board(self, moderator, board):
        self.authorize_action(moderator, ModeratorAction.BOARD_DELETE)
        g.board_service.delete_board(board)

    def user_update_board_config(self, moderator, board, board_config, board_config_row, form):
        self.authorize_board_action(moderator, board, ModeratorBoardAction.CONFIG_UPDATE)
        g.config_service.save_from_form(moderator, board_config, board_config_row, form)

    def user_invite_moderator(self, moderator, board, username):
        self.authorize_board_action(moderator, board, ModeratorBoardAction.MODERATOR_ADD)

        invitee = g.moderator_service.find_moderator_username(username)
        if not invitee:
            raise ArgumentError('Moderator not found')

        g.board_service.board_add_moderator(board, invitee)

    def user_remove_moderator(self, moderator, board, username):
        member = g.moderator_service.find_moderator_username(username)
        if not member:
            raise ArgumentError('Moderator not found')

        if self.has_board_roles(member, board, [roles.BOARD_ROLE_CREATOR]):
            raise ArgumentError('Cannot remove creator')

        if moderator == member:
            self.authorize_board_action(moderator, board, ModeratorBoardAction.MODERATOR_REMOVE_SELF)
            g.board_service.board_remove_moderator(board, member)
            return True
        else:
            self.authorize_board_action(moderator, board, ModeratorBoardAction.MODERATOR_REMOVE)
            g.board_service.board_remove_moderator(board, member)
            return False

    def user_update_roles(self, moderator, board, username, roles):
        self.authorize_board_action(moderator, board, ModeratorBoardAction.ROLES_UPDATE)

        subject = g.moderator_service.find_moderator_username(username)
        if not subject:
            raise ArgumentError('Moderator not found')

        if moderator == subject:
            raise ArgumentError('Cannot change self')

        board_moderator = self.get_board_moderator(subject, board)
        if not board_moderator:
            raise ArgumentError('Not a mod of that board')

        changed = set(roles) ^ set(board_moderator.roles)

        if changed:
            added = []
            removed = []
            for i in changed:
                if i not in board_moderator.roles:
                    added.append(i)
                else:
                    removed.append(i)

            for add in added:
                self.authorize_board_action(moderator, board, ModeratorBoardAction.ROLE_ADD, add)
                self.add_board_role(subject, board, add)

            for remove in removed:
                self.authorize_board_action(moderator, board, ModeratorBoardAction.ROLE_REMOVE, remove)
                self.remove_board_role(subject, board, remove)

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

    def authorize_action(self, actor, action):
        if self.has_role(actor, roles.ROLE_ADMIN):
            return

        if action is ModeratorAction.BOARD_CREATE:
            creator_roles = 0
            for board_moderator in actor.board_moderators:
                if roles.BOARD_ROLE_CREATOR in board_moderator.roles:
                    creator_roles += 1

            if creator_roles >= self.BOARDS_PER_MODERATOR:
                raise ArgumentError('Max boards limit reached ({})'.format(self.BOARDS_PER_MODERATOR))
        else:
            raise Exception('Unknown action')

    def authorize_board_action(self, actor, board, action, data=None):
        if self.has_role(actor, roles.ROLE_ADMIN):
            return

        if action is ModeratorBoardAction.ROLES_UPDATE:
            if not self.has_board_roles(actor, board, [roles.BOARD_ROLE_FULL_PERMISSION]):
                raise NoPermissionError()
        elif action is ModeratorBoardAction.MODERATOR_ADD:
            if not self.has_board_roles(actor, board, [roles.BOARD_ROLE_FULL_PERMISSION]):
                raise NoPermissionError()
        elif action is ModeratorBoardAction.MODERATOR_REMOVE:
            if not self.has_board_roles(actor, board, [roles.BOARD_ROLE_FULL_PERMISSION]):
                raise NoPermissionError()
        elif action is ModeratorBoardAction.MODERATOR_REMOVE_SELF:
            pass  # Allow, creator check if done before
        elif action is ModeratorBoardAction.ROLE_ADD:
            adding_role = data
            if adding_role == roles.BOARD_ROLE_CREATOR:
                raise NoPermissionError()
        elif action is ModeratorBoardAction.ROLE_REMOVE:
            removing_role = data
            if removing_role == roles.BOARD_ROLE_CREATOR:
                raise NoPermissionError()
        elif action is ModeratorBoardAction.CONFIG_UPDATE:
            if not self.has_board_roles(actor, board, [roles.BOARD_ROLE_FULL_PERMISSION, roles.BOARD_ROLE_CONFIG]):
                raise NoPermissionError()
        else:
            raise Exception('Unknown board action')

    def get_moderating_boards(self, moderator):
        if self.has_role(moderator, roles.ROLE_ADMIN):
            return g.board_service.get_all_boards()

        return moderator.boards

    def moderates_board(self, moderator, board):
        if self.has_role(moderator, roles.ROLE_ADMIN):
            return True
        return board in moderator.boards

    def board_role_exists(self, role):
        return role is not None and role in roles.ALL_BOARD_ROLES

    def has_board_roles(self, moderator, board, roles):
        if not all(self.board_role_exists(role) for role in roles):
            raise ArgumentError('Invalid board role')

        board_moderator = self.get_board_moderator(moderator, board)
        if board_moderator is None:
            raise ArgumentError('Not a moderator of that board')

        return any(role in board_moderator.roles for role in roles)

    def add_board_role(self, moderator, board, role):
        if not self.board_role_exists(role):
            raise ArgumentError('Invalid board role')

        board_moderator = self.get_board_moderator(moderator, board)
        if board_moderator is None:
            raise ArgumentError('Not a moderator of that board')

        if role in board_moderator.roles:
            raise ArgumentError('Role already added')

        db = get_db()
        board_moderator.roles.append(role)
        db.commit()

    def remove_board_role(self, moderator, board, role):
        if not self.board_role_exists(role):
            raise ArgumentError('Invalid board role')

        board_moderator = self.get_board_moderator(moderator, board)
        if board_moderator is None:
            raise ArgumentError('Not a moderator of that board')

        if role not in board_moderator.roles:
            raise ArgumentError('Role not added')

        db = get_db()
        board_moderator.roles.remove(role)
        db.commit()

    def get_board_moderator(self, moderator, board):
        db = get_db()
        try:
            return db.query(BoardModerator).filter_by(moderator_id=moderator.id, board_id=board.id).one()
        except NoResultFound:
            return None

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
            raise ArgumentError('Role not added')

        moderator.roles.remove(role)

        db = get_db()
        db.commit()

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
        if not self.check_username_validity(username):
            raise ArgumentError('Invalid username')

        db = get_db()
        try:
            return db.query(Moderator).filter_by(username=username).one()
        except NoResultFound:
            return None

    def get_all_moderators(self):
        return get_db().query(Moderator).all()

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
