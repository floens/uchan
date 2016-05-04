from enum import Enum, unique

import config
from uchan import g
from uchan.lib import roles, ArgumentError


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


class VerificationError(Exception):
    def __init__(self, *args):
        Exception.__init__(self, *args)
        self.for_name = None
        self.request_message = None
        self.single_shot = False


@unique
class ModeratorAction(Enum):
    BOARD_CREATE = 1
    BOARD_DELETE = 2


@unique
class ModeratorBoardAction(Enum):
    MODERATOR_ADD = 1
    MODERATOR_REMOVE = 2
    MODERATOR_REMOVE_SELF = 3
    ROLES_UPDATE = 4
    ROLE_ADD = 5
    ROLE_REMOVE = 6
    CONFIG_UPDATE = 7


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


class ActionAuthorizer:
    def authorize_post_action(self, actor, action, post=None, post_details=None, board=None, thread=None):
        if actor is not None and self.has_role(actor, roles.ROLE_ADMIN):
            return

        if action is PostAction.POST_CREATE:
            if g.ban_service.is_request_banned(post_details.ip4, board):
                raise RequestBannedException()

            if config.ENABLE_COOLDOWN_CHECKING:
                suspended, suspend_time = g.ban_service.is_request_suspended(post_details.ip4, board, thread)
                if suspended:
                    e = RequestSuspendedException()
                    e.suspend_time = suspend_time
                    raise e

            board_config_cached = g.board_cache.find_board_config_cached(board.name)
            if board_config_cached.board_config.posting_verification_required:
                if post_details.verification_data is None or \
                        not g.verification_service.data_is_verified(post_details.verification_data):
                    e = VerificationError('[Please verify here first](_{})'.format('/verify/'))
                    e.for_name = 'post'
                    e.request_message = 'posting'
                    raise e

        elif action is PostAction.POST_DELETE or action is PostAction.POST_DELETE_FILE:
            can_delete = False
            req_roles = [roles.BOARD_ROLE_FULL_PERMISSION, roles.BOARD_ROLE_JANITOR]
            if actor is not None and self.has_board_roles(actor, post.thread.board, req_roles):
                can_delete = True
            elif post_details is not None and post_details.password is not None and post_details.password == post.password:
                can_delete = True

            if not can_delete:
                raise NoPermissionError()
        elif action is PostAction.POST_REPORT:
            if post_details.report_verification_data is None or \
                    not g.verification_service.data_is_verified(post_details.report_verification_data):
                e = VerificationError('[Please verify here first](_{})'.format('/verify/'))
                e.for_name = 'report'
                e.request_message = 'reporting'
                raise e
        elif action is PostAction.THREAD_STICKY_TOGGLE or action is PostAction.THREAD_LOCKED_TOGGLE:
            req_roles = [roles.BOARD_ROLE_FULL_PERMISSION]
            if not g.moderator_service.has_board_roles(actor, board, req_roles):
                raise NoPermissionError()
        else:
            raise Exception('Unknown post action')

    def authorize_ban_check_action(self, request, ip4):
        if not g.verification_service.process_request(request, ip4, 'ban_check'):
            e = VerificationError('[Verify here before checking your ban](_{})'.format('/verify/'))
            e.for_name = 'ban_check'
            e.request_message = 'ban checking'
            e.single_shot = True
            raise e

    def authorize_action(self, actor, action):
        if self.has_role(actor, roles.ROLE_ADMIN):
            return

        if action is ModeratorAction.BOARD_CREATE:
            creator_roles = 0
            for board_moderator in actor.board_moderators:
                if roles.BOARD_ROLE_CREATOR in board_moderator.roles:
                    creator_roles += 1

            if creator_roles >= g.moderator_service.BOARDS_PER_MODERATOR:
                raise ArgumentError('Max boards limit reached ({})'.format(g.moderator_service.BOARDS_PER_MODERATOR))
        else:
            raise Exception('Unknown action')

    def authorize_board_action(self, actor, board, action, data=None):
        if self.has_role(actor, roles.ROLE_ADMIN):
            return

        if action is ModeratorBoardAction.ROLES_UPDATE:
            if not self.has_board_roles(actor, board, [roles.BOARD_ROLE_FULL_PERMISSION]):
                raise NoPermissionError()
        elif action is ModeratorBoardAction.ROLE_ADD:
            adding_role = data
            if adding_role == roles.BOARD_ROLE_CREATOR:
                raise NoPermissionError()
        elif action is ModeratorBoardAction.ROLE_REMOVE:
            removing_role = data
            if removing_role == roles.BOARD_ROLE_CREATOR:
                raise NoPermissionError()
        elif action is ModeratorBoardAction.MODERATOR_ADD:
            if not self.has_board_roles(actor, board, [roles.BOARD_ROLE_FULL_PERMISSION]):
                raise NoPermissionError()
        elif action is ModeratorBoardAction.MODERATOR_REMOVE:
            if not self.has_board_roles(actor, board, [roles.BOARD_ROLE_FULL_PERMISSION]):
                raise NoPermissionError()
        elif action is ModeratorBoardAction.MODERATOR_REMOVE_SELF:
            pass  # Allow, creator check is done before
        elif action is ModeratorBoardAction.CONFIG_UPDATE:
            if not self.has_board_roles(actor, board, [roles.BOARD_ROLE_FULL_PERMISSION, roles.BOARD_ROLE_CONFIG]):
                raise NoPermissionError()
        else:
            raise Exception('Unknown board action')

    def authorize_report_action(self, actor, board, report, action):
        if self.has_role(actor, roles.ROLE_ADMIN):
            return

        req_roles = [roles.BOARD_ROLE_FULL_PERMISSION, roles.BOARD_ROLE_JANITOR]
        if not self.has_board_roles(actor, board, req_roles):
            raise NoPermissionError()

    def has_role(self, moderator, role):
        return g.moderator_service.has_role(moderator, role)

    def has_board_roles(self, moderator, board, req_roles):
        return g.moderator_service.has_board_roles(moderator, board, req_roles)
