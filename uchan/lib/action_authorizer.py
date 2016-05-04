from enum import Enum, unique

from uchan import g
from uchan.lib import roles, NoPermissionError, ArgumentError


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
    POST_DELETE = 1
    POST_DELETE_FILE = 2
    POST_REPORT = 3
    THREAD_STICKY_TOGGLE = 4
    THREAD_LOCKED_TOGGLE = 5


class ActionAuthorizer:
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

    def authorize_post_action(self, actor, action, post=None, post_details=None, thread=None):
        if actor is not None and self.has_role(actor, roles.ROLE_ADMIN):
            return

        if action is PostAction.POST_DELETE or action is PostAction.POST_DELETE_FILE:
            can_delete = False
            req_roles = [roles.BOARD_ROLE_FULL_PERMISSION, roles.BOARD_ROLE_JANITOR]
            if actor is not None and self.has_board_roles(actor, post.thread.board, req_roles):
                can_delete = True
            elif post_details is not None and post_details.password is not None and post_details.password == post.password:
                can_delete = True

            if not can_delete:
                raise NoPermissionError()
        elif action is PostAction.POST_REPORT:
            pass
        elif action is PostAction.THREAD_STICKY_TOGGLE or action is PostAction.THREAD_LOCKED_TOGGLE:
            req_roles = [roles.BOARD_ROLE_FULL_PERMISSION]
            if not g.moderator_service.has_board_roles(actor, thread.board, req_roles):
                raise NoPermissionError()
        else:
            raise Exception('Unknown post action')

    def has_role(self, moderator, role):
        return g.moderator_service.has_role(moderator, role)

    def has_board_roles(self, moderator, board, req_roles):
        return g.moderator_service.has_board_roles(moderator, board, req_roles)
