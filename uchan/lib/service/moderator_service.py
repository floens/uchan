from typing import List

from uchan.lib import action_authorizer, roles
from uchan.lib.action_authorizer import ModeratorBoardAction, NoPermissionError
from uchan.lib.exceptions import ArgumentError
from uchan.lib.mod_log import mod_log
from uchan.lib.model import ModeratorLogType, ModeratorModel, BoardModel, BoardModeratorModel, ModeratorLogModel
from uchan.lib.repository import moderators, board_moderators, boards, moderator_logs
from uchan.lib.service import board_service
from uchan.lib.utils import now

MESSAGE_PASSWORD_INCORRECT = 'Password does not match'


# Moderators

def find_moderator_id(moderator_id: int) -> ModeratorModel:
    return moderators.find_by_id(moderator_id)


def find_moderator_username(username: str) -> ModeratorModel:
    return moderators.find_by_username_case_insensitive(username)


def delete_moderator(moderator: ModeratorModel):
    moderators.delete(moderator)


def get_all_moderators(include_boards=False) -> 'List[ModeratorModel]':
    return moderators.get_all(include_boards)


def check_password(moderator: ModeratorModel, password: str):
    moderators.check_password_match(moderator, password)


def set_password(moderator: ModeratorModel, password: str):
    moderators.update_password(moderator, password)


def check_and_set_password(moderator: ModeratorModel, old_password: str, new_password: str):
    check_password(moderator, old_password)
    set_password(moderator, new_password)


# Moderator roles

def role_exists(role):
    return role is not None and role in roles.ALL_ROLES


def has_role(moderator: ModeratorModel, role: str) -> bool:
    return moderators.has_role(moderator, role)


def add_role(moderator: ModeratorModel, role: str):
    moderators.add_role(moderator, role)


def remove_role(moderator: ModeratorModel, role: str):
    moderators.remove_role(moderator, role)


# Board moderators

def get_all_board_moderators_by_moderator(moderator: ModeratorModel) -> 'List[BoardModeratorModel]':
    return board_moderators.get_all_board_moderators_by_moderator(moderator)


def get_all_board_moderators_by_board(board: BoardModel) -> 'List[BoardModeratorModel]':
    return board_moderators.get_all_board_moderators_by_board(board)


def get_all_moderating_boards(moderator: ModeratorModel) -> 'List[BoardModel]':
    return board_moderators.get_all_moderating_boards(moderator)


def moderates_board(moderator: ModeratorModel, board: BoardModel) -> bool:
    return board_moderators.moderator_has_board(moderator, board)


def moderates_board_id(moderator: ModeratorModel, board_id: int) -> bool:
    if has_role(moderator, roles.ROLE_ADMIN):
        return True

    return board_moderators.moderator_has_board_id(moderator, board_id)


# Board moderator roles

def has_any_of_board_roles(moderator: ModeratorModel, board: BoardModel, role_list: 'List[str]'):
    return board_moderators.has_any_of_board_roles(moderator, board, role_list)


def add_board_role(moderator: ModeratorModel, board: BoardModel, role: str):
    return board_moderators.add_board_role(moderator, board, role)


def remove_board_role(moderator: ModeratorModel, board: BoardModel, role: str):
    return board_moderators.remove_board_role(moderator, board, role)


# Board moderator user actions
# Various actions checked with the authorizer

def user_create_board(moderator: ModeratorModel, board_name: str):
    action_authorizer.authorize_action(moderator, action_authorizer.ModeratorAction.BOARD_CREATE)

    # TODO: make this atomic
    board = BoardModel.from_name(board_name)
    board = board_service.add_board(board)
    board_service.add_moderator(board, moderator)
    board_moderators.add_board_role(moderator, board, roles.BOARD_ROLE_CREATOR)
    board_moderators.add_board_role(moderator, board, roles.BOARD_ROLE_FULL_PERMISSION)

    mod_log('Board {} created'.format(board.name))

    return board


def user_delete_board(moderator, board):
    action_authorizer.authorize_action(moderator, action_authorizer.ModeratorAction.BOARD_DELETE)
    board_name = board.name
    board_service.delete_board(board)
    mod_log('Board {} deleted'.format(board_name))


def can_update_board_config(moderator: ModeratorModel, board: BoardModel) -> bool:
    try:
        action_authorizer.authorize_board_action(moderator, board, ModeratorBoardAction.CONFIG_UPDATE)
        return True
    except NoPermissionError:
        return False


# TODO: merge with authorizer
def can_update_advanced_board_configs(moderator: ModeratorModel) -> bool:
    return has_role(moderator, roles.ROLE_ADMIN)


def can_update_roles(moderator: ModeratorModel, board: BoardModel) -> bool:
    try:
        action_authorizer.authorize_board_action(moderator, board, ModeratorBoardAction.ROLES_UPDATE)
        return True
    except NoPermissionError:
        return False


def can_invite_moderator(moderator: ModeratorModel, board: BoardModel):
    try:
        action_authorizer.authorize_board_action(moderator, board, ModeratorBoardAction.MODERATOR_ADD)
        return True
    except NoPermissionError:
        return False


def can_remove_moderator(moderator: ModeratorModel, board: BoardModel):
    try:
        action_authorizer.authorize_board_action(moderator, board, ModeratorBoardAction.MODERATOR_REMOVE)
        return True
    except NoPermissionError:
        return False


def can_delete_board(moderator: ModeratorModel):
    return has_role(moderator, roles.ROLE_ADMIN)


def required_roles_for_viewing_reports():
    return [roles.BOARD_ROLE_FULL_PERMISSION, roles.BOARD_ROLE_JANITOR]


def user_update_board_config(moderator: ModeratorModel, board: BoardModel):
    action_authorizer.authorize_board_action(moderator, board, action_authorizer.ModeratorBoardAction.CONFIG_UPDATE)

    boards.update_config(board)

    log(ModeratorLogType.CONFIG_UPDATE, moderator, board, 'Config updated')


def user_invite_moderator(moderator: ModeratorModel, board: BoardModel, username: str):
    action_authorizer.authorize_board_action(moderator, board, action_authorizer.ModeratorBoardAction.MODERATOR_ADD)

    invitee = find_moderator_username(username)
    if not invitee:
        raise ArgumentError('Moderator not found')

    board_service.add_moderator(board, invitee)

    log(ModeratorLogType.MODERATOR_INVITE, moderator, board, 'Invited {}'.format(invitee.username))


def user_remove_moderator(moderator: ModeratorModel, board: BoardModel, username: str):
    member = find_moderator_username(username)
    if not member:
        raise ArgumentError('Moderator not found')

    if has_any_of_board_roles(member, board, [roles.BOARD_ROLE_CREATOR]):
        raise ArgumentError('Cannot remove creator')

    if moderator.id == member.id:
        action_authorizer.authorize_board_action(moderator, board,
                                                 action_authorizer.ModeratorBoardAction.MODERATOR_REMOVE_SELF)
        board_service.remove_moderator(board, member)
        log(ModeratorLogType.MODERATOR_REMOVE, moderator, board, 'Removed self')
        return True
    else:
        action_authorizer.authorize_board_action(moderator, board,
                                                 action_authorizer.ModeratorBoardAction.MODERATOR_REMOVE)
        board_service.remove_moderator(board, member)
        log(ModeratorLogType.MODERATOR_REMOVE, moderator, board, 'Removed {}'.format(member.username))
        return False


def user_update_roles(moderator: ModeratorModel, board: BoardModel, username: str, new_roles: 'List[str]'):
    action_authorizer.authorize_board_action(moderator, board, action_authorizer.ModeratorBoardAction.ROLES_UPDATE)

    subject = find_moderator_username(username)
    if not subject:
        raise ArgumentError('Moderator not found')

    if moderator.id == subject.id:  # and not has_role(moderator, roles.ROLE_ADMIN):
        raise ArgumentError('Cannot change self')

    board_moderator = board_moderators.get_board_moderator(board, subject)
    if not board_moderator:
        raise ArgumentError('Not a mod of that board')

    changed = set(new_roles) ^ set(board_moderator.roles)
    # creator is unchangeable
    if roles.BOARD_ROLE_CREATOR in changed:
        changed.remove(roles.BOARD_ROLE_CREATOR)

    if changed:
        added_roles = []
        removed_roles = []
        for i in changed:
            if i not in board_moderator.roles:
                added_roles.append(i)
            else:
                removed_roles.append(i)

        for add in added_roles:
            action_authorizer.authorize_board_action(
                moderator, board, action_authorizer.ModeratorBoardAction.ROLE_ADD, (subject, add))
            add_board_role(subject, board, add)
            log(ModeratorLogType.MODERATOR_ROLE_ADD, moderator, board,
                'Added role {} to {}'.format(add, subject.username))

        for remove in removed_roles:
            action_authorizer.authorize_board_action(
                moderator, board, action_authorizer.ModeratorBoardAction.ROLE_REMOVE, (subject, remove))
            remove_board_role(subject, board, remove)
            log(ModeratorLogType.MODERATOR_ROLE_REMOVE, moderator, board,
                'Removed role {} from {}'.format(remove, subject.username))


def user_register(username: str, password: str, password_repeat: str):
    """
    Register a moderator with the given passwords. The created moderator has no roles and no relationships to boards.
    :param username: username to register with
    :param password: password to register with
    :param password_repeat: repeated version of password, used for the error message.
    :raises ArgumentError if the two passwords don't match.
    :raises ArgumentError any error defined in :meth:`uchan.lib.repository.moderators.create_with_password`
    :return: the created moderator
    """

    if password != password_repeat:
        raise ArgumentError(MESSAGE_PASSWORD_INCORRECT)

    moderator = ModeratorModel.from_username(username)
    moderators.create_with_password(moderator, password)

    mod_log('User {} registered'.format(username))

    return moderator


def user_get_logs(moderator: ModeratorModel, board: BoardModel, page: int, per_page: int) -> 'List[ModeratorLogModel]':
    action_authorizer.authorize_board_action(moderator, board, action_authorizer.ModeratorBoardAction.VIEW_LOG)

    return moderator_logs.get_all_logs_by_board(board, page * per_page, per_page)


def log(log_type: ModeratorLogType, moderator: ModeratorModel, board: BoardModel, text: str):
    log_model = ModeratorLogModel.from_date_type_text_moderator_board(
        date=now(), type=log_type.value, text=text, moderator=moderator, board=board)

    moderator_logs.create(log_model)
