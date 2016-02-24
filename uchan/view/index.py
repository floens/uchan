from flask import render_template

from uchan import app, g
from uchan.lib.service import PageService


@app.route('/')
def index():
    page = g.page_service.get_page_for_type(PageService.TYPE_FRONT_PAGE)

    return render_template('index.html', page=page)
