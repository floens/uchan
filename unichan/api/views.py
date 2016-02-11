from flask import jsonify

from unichan import g
from unichan.api import api


@api.route('/')
def api_index():
    return jsonify({
        'api': 'here'
    })


@api.route('/catalog/<board_name>')
def api_catalog(board_name):
    board_cached = g.posts_cache.find_board_cached(board_name)

    threads = []
    for thread in board_cached.threads:
        posts = []

        for post in thread.posts:
            posts.append({
                'text': post.text
            })

        threads.append({
            'posts': posts
        })

    return jsonify({
        'threads': threads
    })
