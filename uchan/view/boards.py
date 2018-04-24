from flask import render_template

from uchan import app
from uchan.lib.service import board_service
from uchan.view.paged_model import PagedModel


class PagedBoards(PagedModel):
    def provide_count(self):
        return board_service.get_board_count()

    def provide_data(self, offset: int, limit: int):
        return board_service.get_all_boards_with_last_threads((offset, limit))

    def limit(self):
        return 50


@app.route('/boards')
def boards():
    paged_boards = PagedBoards()

    return render_template('boards.html', paged_boards=paged_boards)
