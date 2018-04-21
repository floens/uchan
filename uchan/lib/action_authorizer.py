from enum import Enum, unique

from uchan import configuration
from uchan.lib import roles
from uchan.lib.exceptions import ArgumentError
from uchan.lib.model import ModeratorModel, BoardModel

MESSAGE_REGISTRATION_DISABLED = 'Registration is disabled'
MESSAGE_BOARD_CREATION_DISABLED = 'Board creation is disabled'


class NoPermissionError(Exception):
    def __init__(self, *args):
        Exception.__init__(self, *args)


class RequestBannedException(ArgumentError):
    def __init__(self, *args):
        ArgumentError.__init__(self, *args)


class RequestSuspendedException(ArgumentError):
    def __init__(self, *args):
        ArgumentError.__init__(self, *args)
        self.suspend_time = 0


@unique
class ModeratorAction(Enum):
    BOARD_CREATE = 1
    BOARD_DELETE = 2
    BAN = 3


@unique
class ModeratorBoardAction(Enum):
    MODERATOR_ADD = 1
    MODERATOR_REMOVE = 2
    MODERATOR_REMOVE_SELF = 3
    ROLES_UPDATE = 4
    ROLE_ADD = 5
    ROLE_REMOVE = 6
    CONFIG_UPDATE = 7
    VIEW_LOG = 8


@unique
class ReportAction(Enum):
    REPORT_CLEAR = 1


@unique
class PostAction(Enum):
    POST_CREATE = 1
    POST_DELETE = 2
    POST_DELETE_FILE = 3
    POST_REPORT = 4
    THREAD_STICKY_TOGGLE = 5
    THREAD_LOCKED_TOGGLE = 6


def authorize_registration():
    registration = site_service.get_site_config().registration
    if not registration:
        raise ArgumentError(MESSAGE_REGISTRATION_DISABLED)


def authorize_post_action(actor: ModeratorModel, action: PostAction, post=None, post_details=None, board=None,
                          thread=None):
    if actor is not None and has_role(actor, roles.ROLE_ADMIN):
        return

    if action is PostAction.POST_CREATE:
        if ban_service.is_request_banned(post_details.ip4, board):
            raise RequestBannedException()

        if configuration.app.enable_cooldown_checking:
            suspended, suspend_time = ban_service.is_request_suspended(post_details.ip4, board, thread)
            if suspended:
                e = RequestSuspendedException()
                e.suspend_time = suspend_time
                raise e

    elif action is PostAction.POST_DELETE or action is PostAction.POST_DELETE_FILE:
        can_delete = False
        req_roles = [roles.BOARD_ROLE_FULL_PERMISSION, roles.BOARD_ROLE_JANITOR]
        if actor is not None and has_board_roles(actor, post.thread.board, req_roles):
            can_delete = True
        elif post_details is not None and post_details.password is not None and post_details.password == post.password:
            can_delete = True

        if not can_delete:
            raise NoPermissionError()
    elif action is PostAction.POST_REPORT:
        pass
    elif action is PostAction.THREAD_STICKY_TOGGLE or action is PostAction.THREAD_LOCKED_TOGGLE:
        req_roles = [roles.BOARD_ROLE_FULL_PERMISSION]
        if not moderator_service.has_any_of_board_roles(actor, board, req_roles):
            raise NoPermissionError()
    else:
        raise Exception('Unknown post action')


def authorize_action(actor: ModeratorModel, action: ModeratorAction):
    if has_role(actor, roles.ROLE_ADMIN):
        return

    if action is ModeratorAction.BOARD_CREATE:
        board_creation_enabled = site_service.get_site_config().board_creation
        if not board_creation_enabled:
            raise ArgumentError(MESSAGE_BOARD_CREATION_DISABLED)

        creator_roles = 0
        for board_moderator in moderator_service.get_all_board_moderators_by_moderator(actor):
            if roles.BOARD_ROLE_CREATOR in board_moderator.roles:
                creator_roles += 1

        max = configuration.app.max_boards_per_moderator
        if creator_roles >= max:
            raise ArgumentError('Max boards limit reached ({})'.format(max))
    elif action is ModeratorAction.BOARD_DELETE:
        # must be admin
        raise NoPermissionError()
    elif action is ModeratorAction.BAN:
        # must be admin
        raise NoPermissionError()
    else:
        raise Exception('Unknown action')


def authorize_board_action(actor: ModeratorModel, board: BoardModel, action: ModeratorBoardAction, data=None):
    if has_role(actor, roles.ROLE_ADMIN):
        return

    if action is ModeratorBoardAction.ROLES_UPDATE:
        if not has_board_roles(actor, board, [roles.BOARD_ROLE_FULL_PERMISSION]):
            raise NoPermissionError()
    elif action is ModeratorBoardAction.ROLE_ADD:
        subject, adding_role = data

        if has_board_roles(subject, board, [roles.BOARD_ROLE_CREATOR]):
            raise NoPermissionError()

        if adding_role == roles.BOARD_ROLE_CREATOR:
            raise NoPermissionError()
    elif action is ModeratorBoardAction.ROLE_REMOVE:
        subject, removing_role = data

        if has_board_roles(subject, board, [roles.BOARD_ROLE_CREATOR]):
            raise NoPermissionError()

        if removing_role == roles.BOARD_ROLE_CREATOR:
            raise NoPermissionError()
    elif action is ModeratorBoardAction.MODERATOR_ADD:
        if not has_board_roles(actor, board, [roles.BOARD_ROLE_FULL_PERMISSION]):
            raise NoPermissionError()
    elif action is ModeratorBoardAction.MODERATOR_REMOVE:
        if not has_board_roles(actor, board, [roles.BOARD_ROLE_FULL_PERMISSION]):
            raise NoPermissionError()
    elif action is ModeratorBoardAction.MODERATOR_REMOVE_SELF:
        pass  # Allow, creator check is done before
    elif action is ModeratorBoardAction.CONFIG_UPDATE:
        if not has_board_roles(actor, board, [roles.BOARD_ROLE_FULL_PERMISSION, roles.BOARD_ROLE_CONFIG]):
            raise NoPermissionError()
    elif action is ModeratorBoardAction.VIEW_LOG:
        if not moderator_service.moderates_board(actor, board):
            raise NoPermissionError()
    else:
        raise Exception('Unknown board action')


def authorize_report_action(actor, board, report, action):
    if has_role(actor, roles.ROLE_ADMIN):
        return

    req_roles = [roles.BOARD_ROLE_FULL_PERMISSION, roles.BOARD_ROLE_JANITOR]
    if not has_board_roles(actor, board, req_roles):
        raise NoPermissionError()


def has_role(moderator, role):
    return moderator_service.has_role(moderator, role)


def has_board_roles(moderator, board, req_roles):
    return moderator_service.has_any_of_board_roles(moderator, board, req_roles)


from uchan.lib.service import ban_service, moderator_service, site_service
