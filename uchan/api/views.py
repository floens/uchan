from flask import abort

from uchan.api import api, jsonres
from uchan.lib.cache import posts_cache
from uchan.lib.utils import valid_id_range


@api.route('/')
@jsonres()
def api_index():
    return {
        'version': 'unstable'
    }


@api.route('/catalog/<board_name>')
@jsonres()
def api_catalog(board_name):
    board_cached = posts_cache.find_board_cached(board_name)
    if not board_cached:
        abort(404)

    threads = []
    for thread in board_cached.threads:
        threads.append(build_thread_object(thread))

    return {
        'threads': threads
    }


@api.route('/thread/<string(maxlength=20):board_name>/<int:thread_refno>')
@jsonres()
def api_thread(board_name, thread_refno):
    valid_id_range(thread_refno)

    thread_cached = posts_cache.find_thread_cached(board_name, thread_refno)
    if not thread_cached:
        abort(404)

    return {
        'thread': build_thread_object(thread_cached)
    }


def build_thread_object(thread):
    thread_obj = {
        'id': thread.id,
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


def build_post_object(post):
    post_obj = {
        'id': post.id,
        'refno': post.refno,
        'date': post.date
    }

    if post.html:
        post_obj['html'] = post.html

    if post.name:
        post_obj['name'] = post.name

    if post.subject:
        post_obj['subject'] = post.subject

    if post.mod_code:
        post_obj['modCode'] = post.mod_code

    if post.has_file:
        file_obj = {
            'location': post.file_location,
            'thumbnailLocation': post.file_thumbnail_location,
            'name': post.file_name,
            'width': post.file_width,
            'height': post.file_height,
            'size': post.file_size,
            'thumbnailWidth': post.file_thumbnail_width,
            'thumbnailHeight': post.file_thumbnail_height
        }

        post_obj['file'] = file_obj

    return post_obj
