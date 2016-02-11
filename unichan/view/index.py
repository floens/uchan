from flask import render_template

from unichan import app, g


@app.route('/')
def index():
    boards = g.board_cache.all_boards()

    return render_template('index.html', boards=boards.boards)
