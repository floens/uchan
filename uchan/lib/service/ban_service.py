"""Takes care of bans and post cooldowns"""

from typing import Tuple

from uchan.lib.exceptions import ArgumentError
from uchan.lib.mod_log import mod_log
from uchan.lib.model import BanModel, BoardModel, ThreadModel
from uchan.lib.proxy_request import get_request_ip4
from uchan.lib.repository import bans, posts
from uchan.lib.service import board_service
from uchan.lib.utils import ip4_to_str, now

NEW_THREAD_COOLDOWN = 600 * 1000
NEW_POST_COOLDOWN = 60 * 1000
MAX_BAN_TIME = 24 * 31 * 60 * 60 * 1000
MAX_REASON_LENGTH = 2000

MESSAGE_BAN_TOO_LONG = "Ban too long"
MESSAGE_IP4_ILLEGAL_RANGE = "ip4 end must be bigger than ip4"
MESSAGE_BOARD_NOT_FOUND = "Board not found"
MESSAGE_BAN_TEXT_TOO_LONG = "Ban reason text too long"


def is_request_banned(ip4, board):
    bans = find_bans(ip4, board)
    return len(bans) > 0


def is_request_suspended(
    ip4: int, board: BoardModel, thread: ThreadModel
) -> Tuple[bool, int]:
    timeout = NEW_THREAD_COOLDOWN if thread is None else NEW_POST_COOLDOWN
    from_time = now() - timeout

    post_list = posts.find_posts_by_ip4_from_time(ip4, from_time, by_thread=thread)

    if post_list:
        most_recent = post_list[0]
        time_left = (most_recent.date + timeout - now()) // 1000
        return True, time_left
    return False, 0


def get_request_bans(clear_if_expired=False):
    ip4 = get_request_ip4()
    return find_bans(ip4, clear_if_expired=clear_if_expired)


def find_bans(ip4: int, board: BoardModel = None, clear_if_expired=False):
    ban_list = bans.find_by_ip4(ip4, board)

    applied_bans = list(filter(lambda i: ban_applies(i, ip4, board), ban_list))

    if clear_if_expired:
        # Delete the ban after the user has seen it when it expired
        for ban in filter(lambda i: ban_expired(i), ban_list):
            delete_ban(ban)

    return applied_bans


def ban_applies(ban: BanModel, ip4: int, board: BoardModel) -> bool:
    if ban.board and board and ban.board != board.name:
        return False

    if ban.ip4_end is not None:
        return ban.ip4 < ip4 < ban.ip4_end
    else:
        return ban.ip4 == ip4


def ban_expired(ban: BanModel) -> bool:
    if ban.length == 0:
        return False
    return now() > ban.date + ban.length


def add_ban(ban: BanModel) -> BanModel:
    if ban.length > MAX_BAN_TIME:
        raise ArgumentError(MESSAGE_BAN_TOO_LONG)

    if ban.ip4_end is not None and ban.ip4_end <= ban.ip4:
        raise ArgumentError(MESSAGE_IP4_ILLEGAL_RANGE)

    if ban.board:
        board = board_service.find_board(ban.board)
        if not board:
            raise ArgumentError(MESSAGE_BOARD_NOT_FOUND)

    if ban.reason and len(ban.reason) > MAX_REASON_LENGTH:
        raise ArgumentError(MESSAGE_BAN_TEXT_TOO_LONG)

    ban.date = now()

    ban = bans.create_ban(ban)

    for_board_text = " on {}".format(ban.board) if ban.board else ""
    ip4_end_text = ip4_to_str(ban.ip4_end) if ban.ip4_end is not None else "-"
    f = "ban add {} from {} to {}{} for {} hours reason {}"
    text = f.format(
        ban.id,
        ip4_to_str(ban.ip4),
        ip4_end_text,
        for_board_text,
        ban.length / 60 / 60 / 1000,
        ban.reason,
    )
    mod_log(text)

    return ban


def delete_ban(ban: BanModel):
    bans.delete_ban(ban)


def find_ban_id(ban_id) -> BanModel:
    return bans.find_by_id(ban_id)
