import random
import string

from uchan.lib import action_authorizer, plugin_manager
from uchan.lib.action_authorizer import PostAction
from uchan.lib.crypt_code_compat import generate_crypt_code
from uchan.lib.exceptions import ArgumentError
from uchan.lib.mod_log import mod_log
from uchan.lib.model import (
    BoardModel,
    FileModel,
    PostModel,
    PostResultModel,
    RegCodeModel,
    ThreadModel,
)
from uchan.lib.repository import posts, regcode
from uchan.lib.service import board_service, moderator_service, site_service
from uchan.lib.tasks.post_task import PostDetails
from uchan.lib.utils import ip4_to_str, now

MAX_NAME_LENGTH = 35
MAX_SUBJECT_LENGTH = 100
MIN_PASSWORD_LENGTH = 5
MAX_PASSWORD_LENGTH = 25
MAX_TEXT_LENGTH = 2000
MAX_TEXT_LINES = 25
MAX_TEXT_LENGTH_OP = 6000
MAX_TEXT_LINES_OP = 60

MESSAGE_BOARD_NOT_FOUND = "Board not found"
MESSAGE_THREAD_NOT_FOUND = "Thread not found"
MESSAGE_MODERATOR_NOT_FOUND = "Moderator not found"
MESSAGE_THREAD_LOCKED = "Thread is locked"
MESSAGE_FILE_POSTING_DISABLED = "File posting is disabled"
MESSAGE_FILES_TOO_MANY = "Too many files"
MESSAGE_POST_NO_TEXT = "No text"
MESSAGE_POST_TEXT_TOO_LONG = "Text too long"
MESSAGE_POST_TEXT_TOO_MANY_LINES = "Too many lines"
MESSAGE_POST_NAME_TOO_LONG = "Name too long"
MESSAGE_PASSWORD_TOO_SHORT = "Password too short, at least {} characters required"
MESSAGE_PASSWORD_TOO_LONG = "Password too long, at most {} characters allowed"


def create_post(post_details: PostDetails) -> PostResultModel:
    start_time = now()

    board = board_service.find_board(post_details.board_name)
    if not board:
        raise ArgumentError(MESSAGE_BOARD_NOT_FOUND)

    to_thread = None
    if post_details.thread_refno is not None:
        to_thread = posts.find_thread_by_board_name_thread_refno(
            board.name, post_details.thread_refno
        )
        if to_thread is None:
            raise ArgumentError(MESSAGE_THREAD_NOT_FOUND)

    _check_post_details(post_details, to_thread, board)

    plugin_manager.execute_hook("on_handle_post", post_details)

    site_config = site_service.get_site_config()
    default_name = site_config.default_name

    # Get moderator if mod_id was set
    moderator = None
    if post_details.mod_id is not None:
        moderator = moderator_service.find_moderator_id(post_details.mod_id)
        if moderator is None:
            raise Exception("Moderator not found")

    post = PostModel()
    post.date = now()
    post.ip4 = post_details.ip4

    if moderator is not None and moderator_service.moderates_board(moderator, board):
        post.moderator = moderator

    _handle_text(post, post_details)
    sage = _handle_name(post, post_details, default_name)
    _handle_subject(post, post_details, to_thread)
    _handle_password(post, post_details)

    if post_details.uploaded_files is not None:
        files = []
        for uploaded_file in post_details.uploaded_files:
            # TODO
            file = FileModel()
            file.location = uploaded_file.location
            file.thumbnail_location = uploaded_file.thumbnail_location
            file.original_name = uploaded_file.original_name
            file.width = uploaded_file.width
            file.height = uploaded_file.height
            file.size = uploaded_file.size
            file.thumbnail_width = uploaded_file.thumbnail_width
            file.thumbnail_height = uploaded_file.thumbnail_height
            files.append(file)
        post.files = files

    handle_time = now() - start_time

    if to_thread is None:
        res, insert_time, cache_time = posts.create_thread(board, post)
    else:
        res, insert_time, cache_time = posts.create_post(board, to_thread, post, sage)

    _log_post(post_details, res, handle_time + insert_time, cache_time)

    return res


def _log_post(
    post_details: PostDetails, result: PostResultModel, insert_time, cache_time
):
    total = insert_time + cache_time + post_details.file_time
    file_time_str = (
        "file: {}ms, ".format(post_details.file_time) if post_details.file_time else ""
    )
    s = "{}db: {}ms, caches: {}ms, total: {}ms"
    timings = s.format(file_time_str, insert_time, cache_time, total)
    post_type = "thread" if result.post_refno == 1 else "reply"
    log = "new {} /{}/{}#{} ({})".format(
        post_type, result.board_name, result.thread_refno, result.post_refno, timings
    )
    mod_log(log, ip4_str=ip4_to_str(post_details.ip4))


def _check_post_details(
    post_details: PostDetails, thread: ThreadModel, board: BoardModel
):
    plugin_manager.execute_hook("on_handle_post_check", post_details)

    # Get moderator if mod_id was set
    moderator = None
    if post_details.mod_id is not None:
        moderator = moderator_service.find_moderator_id(post_details.mod_id)
        if moderator is None:
            raise Exception(MESSAGE_MODERATOR_NOT_FOUND)

    if thread and thread.locked:
        raise ArgumentError(MESSAGE_THREAD_LOCKED)

    action_authorizer.authorize_post_action(
        moderator,
        PostAction.POST_CREATE,
        post_details=post_details,
        board=board,
        thread=thread,
    )

    if post_details.has_files and not board.config.file_posting:
        raise ArgumentError(MESSAGE_FILE_POSTING_DISABLED)

    if (
        post_details.has_files
        and len(post_details.uploaded_files) > board.config.max_files
    ):
        raise ArgumentError(MESSAGE_FILES_TOO_MANY)

    # Allow no text when an image is attached
    if (
        not post_details.text or not post_details.text.strip()
    ) and not post_details.has_files:
        raise ArgumentError(MESSAGE_POST_NO_TEXT)

    if post_details.text is not None:
        max_length = MAX_TEXT_LENGTH_OP if thread is None else MAX_TEXT_LENGTH
        max_lines = MAX_TEXT_LINES_OP if thread is None else MAX_TEXT_LINES

        if len(post_details.text) > max_length:
            raise ArgumentError(MESSAGE_POST_TEXT_TOO_LONG)

        if len(post_details.text.splitlines()) > max_lines:
            raise ArgumentError(MESSAGE_POST_TEXT_TOO_MANY_LINES)

    if post_details.name is not None and len(post_details.name) > MAX_NAME_LENGTH:
        raise ArgumentError(MESSAGE_POST_NAME_TOO_LONG)

    if post_details.password is not None:
        if len(post_details.password) < MIN_PASSWORD_LENGTH:
            raise ArgumentError(MESSAGE_PASSWORD_TOO_SHORT.format(MIN_PASSWORD_LENGTH))

        if len(post_details.password) > MAX_PASSWORD_LENGTH:
            raise ArgumentError(MESSAGE_PASSWORD_TOO_LONG.format(MAX_PASSWORD_LENGTH))


def _handle_text(post, post_details):
    if post_details.text is not None:
        post.text = post_details.text.strip()
    else:
        post.text = ""


def _handle_password(post, post_details):
    if post_details.password is not None:
        post.password = post_details.password


def _handle_subject(post, post_details, to_thread):
    if to_thread is None and post_details.subject is not None:
        post.subject = post_details.subject


def _handle_name(post, post_details, default_name):
    sage = False
    result_name = None

    if post_details.name is not None:
        stripped_name = post_details.name.strip()
        if stripped_name:
            sage, result_name = _process_name(stripped_name)

    if result_name:
        post.name = result_name
    else:
        post.name = default_name

    return sage


def _process_name(name):
    sage = False
    result_name = None

    if "##" in name:
        name, password = _name_password_from_name(name, "##")
        name = _filter_name(name)

        if password:
            existing_regcode = regcode.find_for_password(password)
            if existing_regcode:
                cap = existing_regcode.code
            else:
                new_regcode = RegCodeModel.from_code(_generate_capcode())
                new_regcode = regcode.create(new_regcode, password)
                cap = new_regcode.code

            result_name = name + " !!" + cap
    elif "#" in name:
        name, password = _name_password_from_name(name, "#")
        name = _filter_name(name)

        if password:
            # Styling is applied later
            cap = generate_crypt_code(password)
            result_name = name + " !" + cap
    elif name.lower() == "sage" or name == "下げ":
        sage = True
    else:
        name = _filter_name(name)
        if name:
            result_name = name

    return sage, result_name


def _name_password_from_name(name, divider):
    name, password = name.split(divider, maxsplit=1)
    return name, password


def _filter_name(name):
    return name.replace("!", "")


def _generate_capcode():
    sys_random = random.SystemRandom()

    length = 10
    alphabet = string.ascii_letters + string.digits + "+."

    return "".join(sys_random.choice(alphabet) for _ in range(length))
