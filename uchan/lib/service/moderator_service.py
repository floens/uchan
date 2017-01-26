import string

import bcrypt
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound

USERNAME_MAX_LENGTH = 50
USERNAME_ALLOWED_CHARS = string.ascii_letters + string.digits + '_'
PASSWORD_MIN_LENGTH = 6
PASSWORD_MAX_LENGTH = 255
PASSWORD_ALLOWED_CHARS = string.ascii_letters + string.digits + string.punctuation + '_'

BOARDS_PER_MODERATOR = 2

from uchan.lib import ArgumentError, action_authorizer, roles
from uchan.lib.database import get_db
from uchan.lib.mod_log import mod_log
from uchan.lib.models import BoardModerator, ModeratorLog, Moderator
from uchan.lib.models.moderator_log import ModeratorLogType
from uchan.lib.service import board_service, config_service
from uchan.lib.utils import now


def user_create_board(moderator, board):
    action_authorizer.authorize_action(moderator, action_authorizer.ModeratorAction.BOARD_CREATE)

    board_service.add_board(board)
    board_service.board_add_moderator(board, moderator)
    add_board_role(moderator, board, roles.BOARD_ROLE_CREATOR)
    add_board_role(moderator, board, roles.BOARD_ROLE_FULL_PERMISSION)

    mod_log('Board {} created'.format(board.name))

    return board


def user_delete_board(moderator, board):
    action_authorizer.authorize_action(moderator, action_authorizer.ModeratorAction.BOARD_DELETE)
    board_name = board.name
    board_service.delete_board(board)
    mod_log('Board {} deleted'.format(board_name))


def user_update_board_config(moderator, board, board_config, board_config_row, form):
    action_authorizer.authorize_board_action(moderator, board, action_authorizer.ModeratorBoardAction.CONFIG_UPDATE)
    config_service.save_from_form(moderator, board_config, board_config_row, form)
    log(ModeratorLogType.CONFIG_UPDATE, moderator, board, 'Config updated')


def user_invite_moderator(moderator, board, username):
    action_authorizer.authorize_board_action(moderator, board, action_authorizer.ModeratorBoardAction.MODERATOR_ADD)

    invitee = find_moderator_username(username)
    if not invitee:
        raise ArgumentError('Moderator not found')

    board_service.board_add_moderator(board, invitee)

    log(ModeratorLogType.MODERATOR_INVITE, moderator, board, 'Invited {}'.format(invitee.username))


def user_remove_moderator(moderator, board, username):
    member = find_moderator_username(username)
    if not member:
        raise ArgumentError('Moderator not found')

    if has_board_roles(member, board, [roles.BOARD_ROLE_CREATOR]):
        raise ArgumentError('Cannot remove creator')

    if moderator == member:
        action_authorizer.authorize_board_action(moderator, board,
                                                 action_authorizer.ModeratorBoardAction.MODERATOR_REMOVE_SELF)
        board_service.board_remove_moderator(board, member)
        log(ModeratorLogType.MODERATOR_REMOVE, moderator, board, 'Removed self')
        return True
    else:
        action_authorizer.authorize_board_action(moderator, board,
                                                 action_authorizer.ModeratorBoardAction.MODERATOR_REMOVE)
        board_service.board_remove_moderator(board, member)
        log(ModeratorLogType.MODERATOR_REMOVE, moderator, board, 'Removed {}'.format(member.username))
        return False


def user_update_roles(moderator, board, username, new_roles):
    action_authorizer.authorize_board_action(moderator, board, action_authorizer.ModeratorBoardAction.ROLES_UPDATE)

    subject = find_moderator_username(username)
    if not subject:
        raise ArgumentError('Moderator not found')

    if moderator == subject and not has_role(moderator, roles.ROLE_ADMIN):
        raise ArgumentError('Cannot change self')

    board_moderator = get_board_moderator(subject, board)
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
            action_authorizer.authorize_board_action(moderator, board, action_authorizer.ModeratorBoardAction.ROLE_ADD,
                                                     add)
            add_board_role(subject, board, add)
            log(ModeratorLogType.MODERATOR_ROLE_ADD, moderator, board,
                'Added role {} to {}'.format(add, subject.username))

        for remove in removed:
            action_authorizer.authorize_board_action(moderator, board,
                                                     action_authorizer.ModeratorBoardAction.ROLE_REMOVE, remove)
            remove_board_role(subject, board, remove)
            log(ModeratorLogType.MODERATOR_ROLE_REMOVE, moderator, board,
                'Removed role {} from {}'.format(remove, subject.username))


def user_register(username, password, password_repeat):
    if not check_username_validity(username):
        raise ArgumentError('Invalid username')

    if not check_password_validity(password) or not check_password_validity(password_repeat):
        raise ArgumentError('Invalid password')

    if password != password_repeat:
        raise ArgumentError('Password does not match')

    if find_moderator_username(username) is not None:
        raise ArgumentError('Username taken')

    moderator = Moderator()
    moderator.roles = []
    moderator.username = username

    create_moderator(moderator, password)

    mod_log('User {} registered'.format(username))

    return moderator


def user_get_logs(moderator, board, page, per_page):
    action_authorizer.authorize_board_action(moderator, board, action_authorizer.ModeratorBoardAction.VIEW_LOG)

    db = get_db()
    logs = db.query(ModeratorLog) \
        .filter(ModeratorLog.board == board) \
        .order_by(desc(ModeratorLog.date)) \
        .options(joinedload('moderator')) \
        .offset(page * per_page).limit(per_page).all()
    return logs


def log(log_type: ModeratorLogType, moderator, board, text):
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


def get_moderating_boards(moderator):
    return moderator.boards


def moderates_board(moderator, board):
    if has_role(moderator, roles.ROLE_ADMIN):
        return True
    return board in moderator.boards


def moderates_board_id(moderator, board_id):
    if has_role(moderator, roles.ROLE_ADMIN):
        return True
    db = get_db()
    try:
        db.query(BoardModerator).filter_by(moderator_id=moderator.id, board_id=board_id).one()
        return True
    except NoResultFound:
        return False


def board_role_exists(role):
    return role is not None and role in roles.ALL_BOARD_ROLES


def has_board_roles(moderator, board, roles):
    if not all(board_role_exists(role) for role in roles):
        raise ArgumentError('Invalid board role')

    board_moderator = get_board_moderator(moderator, board)
    if board_moderator is None:
        return False

    return any(role in board_moderator.roles for role in roles)


def add_board_role(moderator, board, role):
    if not board_role_exists(role):
        raise ArgumentError('Invalid board role')

    board_moderator = get_board_moderator(moderator, board)
    if board_moderator is None:
        raise ArgumentError('Not a moderator of that board')

    if role in board_moderator.roles:
        raise ArgumentError('Role already added')

    db = get_db()
    board_moderator.roles.append(role)
    db.commit()


def remove_board_role(moderator, board, role):
    if not board_role_exists(role):
        raise ArgumentError('Invalid board role')

    board_moderator = get_board_moderator(moderator, board)
    if board_moderator is None:
        raise ArgumentError('Not a moderator of that board')

    if role not in board_moderator.roles:
        raise ArgumentError('Role not added')

    db = get_db()
    board_moderator.roles.remove(role)
    db.commit()


def get_board_moderator(moderator, board):
    db = get_db()
    try:
        return db.query(BoardModerator).filter_by(moderator_id=moderator.id, board_id=board.id).one()
    except NoResultFound:
        return None


def role_exists(role):
    return role is not None and role in roles.ALL_ROLES


def has_role(moderator, role):
    return role is not None and role in moderator.roles


def add_role(moderator, role):
    if not role_exists(role):
        raise ArgumentError('Invalid role')

    if has_role(moderator, role):
        raise ArgumentError('Role already added')

    moderator.roles.append(role)

    db = get_db()
    db.commit()


def remove_role(moderator, role):
    if not role:
        raise ArgumentError('Invalid role')

    if not has_role(moderator, role):
        raise ArgumentError('Role not added')

    moderator.roles.remove(role)

    db = get_db()
    db.commit()


def check_username_validity(username):
    if not 0 < len(username) <= USERNAME_MAX_LENGTH:
        return False

    if not all(c in USERNAME_ALLOWED_CHARS for c in username):
        return False

    return True


def check_password_validity(password):
    if password is None or len(password) < PASSWORD_MIN_LENGTH or len(password) >= PASSWORD_MAX_LENGTH:
        return False

    if not all(c in PASSWORD_ALLOWED_CHARS for c in password):
        return False

    return True


def create_moderator(moderator, password):
    if not check_username_validity(moderator.username):
        raise ArgumentError('Invalid username')

    if not check_password_validity(password):
        raise ArgumentError('Invalid password')

    moderator.password = hash_password(password)

    db = get_db()

    db.add(moderator)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ArgumentError('Duplicate username')


def delete_moderator(moderator):
    db = get_db()
    db.delete(moderator)
    db.commit()


def find_moderator_id(id):
    db = get_db()
    try:
        return db.query(Moderator).filter_by(id=id).one()
    except NoResultFound:
        return None


def find_moderator_username(username):
    if not check_username_validity(username):
        raise ArgumentError('Invalid username')

    db = get_db()
    try:
        # Username chars are safe because it is checked above
        return db.query(Moderator).filter(Moderator.username.ilike(username)).one()
    except NoResultFound:
        return None


def get_all_moderators():
    return get_db().query(Moderator).all()


def change_password(moderator, old_password, new_password):
    if not check_password_validity(old_password):
        raise ArgumentError('Invalid password')

    check_password(moderator, old_password)

    _update_password(moderator, new_password)


def change_password_admin(moderator, new_password):
    _update_password(moderator, new_password)


def check_password(moderator: Moderator, password: str):
    moderator_hashed_password = moderator.password

    if bcrypt.hashpw(password.encode(), moderator_hashed_password) != moderator_hashed_password:
        raise ArgumentError('Password does not match')


def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())


def _update_password(moderator, new_password):
    if not check_password_validity(new_password):
        raise ArgumentError('Invalid new password')

    moderator.password = hash_password(new_password)

    db = get_db()
    db.commit()
