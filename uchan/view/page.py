from flask import render_template, abort

from uchan import app
from uchan.lib.cache import page_cache


@app.route('/page/<string(maxlength=20):link_name>/')
def view_page(link_name):
    page = page_cache.find_page_cached(link_name)
    if not page:
        abort(404)

    return render_template('page.html', page=page)
