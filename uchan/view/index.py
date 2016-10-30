from flask import render_template

from uchan import app
from uchan.lib.cache import page_cache
from uchan.lib.service import page_service


@app.route('/')
def index():
    front_page_pages = page_cache.find_pages_for_type_cached(page_service.TYPE_FRONT_PAGE)
    page = front_page_pages.pages[0] if front_page_pages and front_page_pages.pages else None

    return render_template('index.html', page=page)
