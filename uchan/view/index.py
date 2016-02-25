from flask import render_template

from uchan import app, g
from uchan.lib.service import PageService


@app.route('/')
def index():
    front_page_pages = g.page_cache.find_pages_for_type_cached(PageService.TYPE_FRONT_PAGE)
    page = front_page_pages.pages[0] if front_page_pages and front_page_pages.pages else None

    return render_template('index.html', page=page)
