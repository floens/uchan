from uchan.lib import action_authorizer
from uchan.lib.action_authorizer import PostAction, NoPermissionError, RequestBannedException
from uchan.lib.exceptions import BadRequestError
from uchan.lib.mod_log import mod_log
from uchan.lib.model import ThreadModel, ModeratorModel, PostModel
from uchan.lib.repository import posts
from uchan.lib.service import ban_service, moderator_service, report_service
from uchan.lib.tasks.post_task import ManagePostDetails
from uchan.lib.utils import ip4_to_str

MESSAGE_THREAD_NOT_FOUND = 'Thread not found'
MESSAGE_NO_POST_ID = 'No post selected'
MESSAGE_POST_NOT_FOUND = 'Post not found'
MESSAGE_DELETE_NO_PERMISSION = 'Password invalid'
MESSAGE_MODERATOR_NOT_FOUND = 'Moderator not found'


def handle_manage_post(details: ManagePostDetails):
    thread = posts.find_thread_by_board_name_thread_refno(details.board_name, details.thread_refno)
    if not thread:
        raise BadRequestError(MESSAGE_THREAD_NOT_FOUND)

    # Get moderator if mod_id was set
    moderator = None
    if details.mod_id is not None:
        moderator = moderator_service.find_moderator_id(details.mod_id)
        if moderator is None:
            raise Exception('Moderator not found')

    # You cannot manage when you are banned
    if ban_service.is_request_banned(details.ip4, thread.board):
        raise RequestBannedException()

    if details.mode == ManagePostDetails.DELETE or details.mode == ManagePostDetails.REPORT:
        _manage_post(details, moderator)
    elif details.mode == ManagePostDetails.TOGGLE_STICKY or details.mode == ManagePostDetails.TOGGLE_LOCKED:
        _manage_thread(thread, details, moderator)
    else:
        raise Exception('Unknown mode')


def _manage_post(details: ManagePostDetails, moderator: ModeratorModel):
    post = posts.find_post_by_id(details.post_id)
    if not post:
        raise BadRequestError(MESSAGE_NO_POST_ID if not details.post_id else MESSAGE_POST_NOT_FOUND)

    if details.mode == ManagePostDetails.DELETE:
        _manage_delete(details, moderator, post)
    elif details.mode == ManagePostDetails.REPORT:
        _manage_report(details, moderator, post)


def _manage_delete(details: ManagePostDetails, moderator: ModeratorModel, post: PostModel):
    try:
        action_authorizer.authorize_post_action(moderator, PostAction.POST_DELETE, post, details)

        message = 'post {} delete'.format(details.post_id)
        mod_log(message, ip4_str=ip4_to_str(details.ip4), moderator=moderator)

        posts.delete_post(post)
    except NoPermissionError as e:
        message = 'post {} delete failed, {}'.format(details.post_id, str(e))
        mod_log(message, ip4_str=ip4_to_str(details.ip4), moderator=moderator)

        raise BadRequestError(MESSAGE_DELETE_NO_PERMISSION)


def _manage_report(details: ManagePostDetails, moderator: ModeratorModel, post: PostModel):
    action_authorizer.authorize_post_action(moderator, PostAction.POST_REPORT, post, details)

    report_service.report_post(post)

    message = 'post {} reported'.format(post.id)
    mod_log(message, ip4_str=ip4_to_str(details.ip4), moderator=moderator)


def _manage_thread(thread: ThreadModel, details: ManagePostDetails, moderator: ModeratorModel):
    if not moderator:
        raise BadRequestError(MESSAGE_MODERATOR_NOT_FOUND)

    if details.mode == ManagePostDetails.TOGGLE_STICKY:
        _manage_sticky_toggle(thread, details, moderator)
    elif details.mode == ManagePostDetails.TOGGLE_LOCKED:
        _manage_locked_toggle(thread, details, moderator)


def _manage_sticky_toggle(thread: ThreadModel, details: ManagePostDetails, moderator: ModeratorModel):
    action_authorizer.authorize_post_action(moderator, PostAction.THREAD_STICKY_TOGGLE, board=thread.board)

    posts.update_thread_sticky(thread, not thread.sticky)

    message = 'sticky on /{}/{} {}'.format(thread.board.name, thread.id, 'disabled' if thread.sticky else 'enabled')
    mod_log(message, ip4_str=ip4_to_str(details.ip4), moderator=moderator)


def _manage_locked_toggle(thread: ThreadModel, details: ManagePostDetails, moderator: ModeratorModel):
    action_authorizer.authorize_post_action(moderator, PostAction.THREAD_LOCKED_TOGGLE, board=thread.board)

    posts.update_thread_locked(thread, not thread.locked)

    message = 'lock on /{}/{} {}'.format(thread.board.name, thread.id, 'disabled' if thread.locked else 'enabled')
    mod_log(message, ip4_str=ip4_to_str(details.ip4), moderator=moderator)
