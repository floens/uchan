from flask import render_template, abort, redirect, url_for

from uchan import app
from uchan import g


@app.route('/page/<link_name>/')
def view_page(link_name):
    page = g.page_service.get_page_for_link_name(link_name)
    if not page:
        abort(404)

    return render_template('page.html', page=page)
