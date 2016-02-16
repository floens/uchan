from flask import render_template, abort, redirect, url_for

from unichan import app, g


@app.route('/<board_name>/view/<int:thread_id>')
def view_thread(board_name, thread_id):
    if thread_id <= 0 or thread_id > 2 ** 32:
        abort(400)

    thread_cached = g.posts_cache.find_thread_cached(thread_id)

    if thread_cached:
        if thread_cached.board.name != board_name:
            abort(404)
        else:
            return render_template('thread.html', thread=thread_cached)
    else:
        abort(404)


@app.route('/find_post/<int:post_id>')
def find_post(post_id):
    if post_id <= 0 or post_id > 2 ** 32:
        abort(400)

    post = g.posts_service.find_post(post_id)
    if post:
        return redirect(url_for('view_thread', board_name=post.thread.board.name, thread_id=post.thread.id) + '#p' + str(post.refno))
    else:
        abort(404)
