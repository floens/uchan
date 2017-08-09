from flask import abort

from uchan.lib.model import BoardModel, ThreadModel, PostModel, CatalogModel
from uchan.lib.service import board_service, posts_service, file_service
from uchan.lib.utils import valid_id_range
from uchan.view.api import api, jsonres


@api.route('/')
@jsonres()
def api_index():
    return {
        'version': 'unstable'
    }


@api.route('/catalog/<board_name>')
@jsonres()
def api_catalog(board_name):
    board: BoardModel = board_service.find_board(board_name)
    if not board:
        abort(404)

    catalog: CatalogModel = posts_service.get_catalog(board)

    return {
        'threads': list(map(lambda i: build_thread_object(i), catalog.threads))
    }


@api.route('/thread/<string(maxlength=20):board_name>/<int:thread_refno>')
@jsonres()
def api_thread(board_name, thread_refno):
    valid_id_range(thread_refno)

    board: BoardModel = board_service.find_board(board_name)
    if not board:
        abort(404)

    thread = posts_service.find_thread_by_board_thread_refno_with_posts(board, thread_refno)
    if not thread:
        abort(404)

    return {
        'thread': build_thread_object(thread)
    }


def build_thread_object(thread: ThreadModel):
    thread_obj = {
        # 'id': thread.id,
        'refno': thread.refno,
        'lastModified': thread.last_modified
    }

    if thread.locked:
        thread_obj['locked'] = True

    if thread.sticky:
        thread_obj['sticky'] = True

    posts = []

    for post in thread.posts:
        posts.append(build_post_object(post))

    thread_obj['posts'] = posts

    return thread_obj


def build_post_object(post: PostModel):
    post_obj = {
        'id': post.id,
        'refno': post.refno,
        'date': post.date
    }

    if post.html_text:
        post_obj['html'] = post.html_text

    if post.name:
        post_obj['name'] = post.name

    if post.subject:
        post_obj['subject'] = post.subject

    if post.mod_code:
        post_obj['modCode'] = post.mod_code

    if post.files:
        files_obj = []
        for file in post.files:
            file_obj = {
                'location': file_service.resolve_to_uri(file.location),
                'thumbnailLocation': file_service.resolve_to_uri(file.thumbnail_location),
                'name': file.original_name,
                'width': file.width,
                'height': file.height,
                'size': file.size,
                'thumbnailWidth': file.thumbnail_width,
                'thumbnailHeight': file.thumbnail_height
            }
            files_obj.append(file_obj)

        post_obj['files'] = files_obj

    return post_obj
