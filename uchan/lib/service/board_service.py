from typing import List, Optional, Tuple

from uchan.lib.model import BoardModel, ModeratorModel, PostModel, ThreadModel
from uchan.lib.repository import board_moderators, boards


def get_all_boards() -> List[BoardModel]:
    return boards.get_all()


def get_all_board_names() -> List[str]:
    return boards.get_all_board_names()


def get_all_boards_with_last_threads(
    offset_limit=None,
) -> List[Tuple[BoardModel, ThreadModel, PostModel]]:
    return boards.get_all_boards_with_last_threads(offset_limit)


def get_board_count() -> int:
    return boards.get_board_count()


def find_board(board_name) -> Optional[BoardModel]:
    return boards.find_by_name(board_name)


def find_by_names(names: List[str]) -> List[BoardModel]:
    return boards.find_by_names(names)


def add_board(board: BoardModel) -> BoardModel:
    return boards.create(board)


def delete_board(board: BoardModel):
    boards.delete(board)


def update_configuration(board: BoardModel):
    return boards.update_config(board)


def add_moderator(board: BoardModel, moderator: ModeratorModel):
    return board_moderators.board_add_moderator(board, moderator)


def remove_moderator(board: BoardModel, moderator: ModeratorModel):
    return board_moderators.board_remove_moderator(board, moderator)
