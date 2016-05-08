import string

import bcrypt
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound

from uchan import g
from uchan.lib import ArgumentError
from uchan.lib import roles
from uchan.lib.action_authorizer import ModeratorAction, ModeratorBoardAction
from uchan.lib.database import get_db
from uchan.lib.mod_log import mod_log
from uchan.lib.models import BoardModerator, ModeratorLog, Moderator
from uchan.lib.models.moderator_log import ModeratorLogType
from uchan.lib.utils import now


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
        g.action_authorizer.authorize_action(moderator, ModeratorAction.BOARD_CREATE)

        g.board_service.add_board(board)
        g.board_service.board_add_moderator(board, moderator)
        self.add_board_role(moderator, board, roles.BOARD_ROLE_CREATOR)
        self.add_board_role(moderator, board, roles.BOARD_ROLE_FULL_PERMISSION)

        mod_log('Board {} created'.format(board.name))

        return board

    def user_delete_board(self, moderator, board):
        g.action_authorizer.authorize_action(moderator, ModeratorAction.BOARD_DELETE)
        board_name = board.name
        g.board_service.delete_board(board)
        mod_log('Board {} deleted'.format(board_name))

    def user_update_board_config(self, moderator, board, board_config, board_config_row, form):
        g.action_authorizer.authorize_board_action(moderator, board, ModeratorBoardAction.CONFIG_UPDATE)
        g.config_service.save_from_form(moderator, board_config, board_config_row, form)
        self.log(ModeratorLogType.CONFIG_UPDATE, moderator, board, 'Config updated')

    def user_invite_moderator(self, moderator, board, username):
        g.action_authorizer.authorize_board_action(moderator, board, ModeratorBoardAction.MODERATOR_ADD)

        invitee = g.moderator_service.find_moderator_username(username)
        if not invitee:
            raise ArgumentError('Moderator not found')

        g.board_service.board_add_moderator(board, invitee)

        self.log(ModeratorLogType.MODERATOR_INVITE, moderator, board, 'Invited {}'.format(invitee.username))

    def user_remove_moderator(self, moderator, board, username):
        member = g.moderator_service.find_moderator_username(username)
        if not member:
            raise ArgumentError('Moderator not found')

        if self.has_board_roles(member, board, [roles.BOARD_ROLE_CREATOR]):
            raise ArgumentError('Cannot remove creator')

        if moderator == member:
            g.action_authorizer.authorize_board_action(moderator, board, ModeratorBoardAction.MODERATOR_REMOVE_SELF)
            g.board_service.board_remove_moderator(board, member)
            self.log(ModeratorLogType.MODERATOR_REMOVE, moderator, board, 'Removed self')
            return True
        else:
            g.action_authorizer.authorize_board_action(moderator, board, ModeratorBoardAction.MODERATOR_REMOVE)
            g.board_service.board_remove_moderator(board, member)
            self.log(ModeratorLogType.MODERATOR_REMOVE, moderator, board, 'Removed {}'.format(member.username))
            return False

    def user_update_roles(self, moderator, board, username, new_roles):
        g.action_authorizer.authorize_board_action(moderator, board, ModeratorBoardAction.ROLES_UPDATE)

        subject = g.moderator_service.find_moderator_username(username)
        if not subject:
            raise ArgumentError('Moderator not found')

        if moderator == subject and not self.has_role(moderator, roles.ROLE_ADMIN):
            raise ArgumentError('Cannot change self')

        board_moderator = self.get_board_moderator(subject, board)
        if not board_moderator:
            raise ArgumentError('Not a mod of that board')

        changed = set(new_roles) ^ set(board_moderator.roles)
        # creator is disabled in the ui so it is always unchecked
        if roles.BOARD_ROLE_CREATOR in changed:
            changed.remove(roles.BOARD_ROLE_CREATOR)

        if changed:
            added = []
            removed = []
            for i in changed:
                if i not in board_moderator.roles:
                    added.append(i)
                else:
                    removed.append(i)

            for add in added:
                g.action_authorizer.authorize_board_action(moderator, board, ModeratorBoardAction.ROLE_ADD, add)
                self.add_board_role(subject, board, add)
                self.log(ModeratorLogType.MODERATOR_ROLE_ADD, moderator, board,
                         'Added role {} to {}'.format(add, subject.username))

            for remove in removed:
                g.action_authorizer.authorize_board_action(moderator, board, ModeratorBoardAction.ROLE_REMOVE, remove)
                self.remove_board_role(subject, board, remove)
                self.log(ModeratorLogType.MODERATOR_ROLE_REMOVE, moderator, board,
                         'Removed role {} from {}'.format(remove, subject.username))

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

    def user_get_logs(self, moderator, board, page, per_page):
        g.action_authorizer.authorize_board_action(moderator, board, ModeratorBoardAction.VIEW_LOG)

        db = get_db()
        logs = db.query(ModeratorLog) \
            .filter(ModeratorLog.board == board) \
            .order_by(desc(ModeratorLog.date)) \
            .options(joinedload('moderator')) \
            .offset(page * per_page).limit(per_page).all()
        return logs

    def log(self, log_type: ModeratorLogType, moderator, board, text):
        db = get_db()
        row = ModeratorLog()
        row.date = now()
        row.type = log_type.value
        row.text = text
        if moderator is not None:
            row.moderator = moderator
        if board is not None:
            row.board = board

        db.add(row)
        db.commit()

    def get_moderating_boards(self, moderator):
        return moderator.boards

    def moderates_board(self, moderator, board):
        if self.has_role(moderator, roles.ROLE_ADMIN):
            return True
        return board in moderator.boards

    def moderates_board_id(self, moderator, board_id):
        if self.has_role(moderator, roles.ROLE_ADMIN):
            return True
        db = get_db()
        try:
            db.query(BoardModerator).filter_by(moderator_id=moderator.id, board_id=board_id).one()
            return True
        except NoResultFound:
            return False

    def board_role_exists(self, role):
        return role is not None and role in roles.ALL_BOARD_ROLES

    def has_board_roles(self, moderator, board, roles):
        if not all(self.board_role_exists(role) for role in roles):
            raise ArgumentError('Invalid board role')

        board_moderator = self.get_board_moderator(moderator, board)
        if board_moderator is None:
            return False

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
            # Username chars are safe because it is checked above
            return db.query(Moderator).filter(Moderator.username.ilike(username)).one()
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
