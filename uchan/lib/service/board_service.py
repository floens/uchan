from typing import List, Optional

from uchan.lib.model import BoardModel, ModeratorModel
from uchan.lib.repository import boards, board_moderators


def get_all_boards() -> 'List[BoardModel]':
    return boards.get_all()


def find_board(board_name, include_config=False) -> 'Optional[BoardModel]':
    return boards.find_by_name(board_name, include_config)


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
