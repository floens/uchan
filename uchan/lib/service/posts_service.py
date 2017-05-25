from typing import Optional

from uchan.lib.model import BoardModel, ThreadModel, PostResultModel, BoardPageModel, CatalogModel, PostModel
from uchan.lib.repository import posts
from uchan.lib.service import post_helper, post_manage_helper
from uchan.lib.tasks.post_task import ManagePostDetails, PostDetails


def create_post(post_details: PostDetails) -> PostResultModel:
    return post_helper.create_post(post_details)


def handle_manage_post(details: ManagePostDetails):
    return post_manage_helper.handle_manage_post(details)


def find_thread_by_board_thread_refno_with_posts(board: BoardModel, thread_refno: int) -> 'Optional[ThreadModel]':
    return posts.find_thread_by_board_thread_refno_with_posts(board, thread_refno)


def get_board_page(board: BoardModel, page: int) -> BoardPageModel:
    return posts.get_board_page(board, page)


def get_catalog(board: BoardModel) -> CatalogModel:
    return posts.get_catalog(board)


def find_post(post_id: int) -> PostModel:
    return posts.find_post_by_id(post_id)


def delete_file(post: PostModel):
    posts.delete_post_file(post)


def delete_post(post: PostModel):
    posts.delete_post(post)
