from flask import render_template, abort

from uchan import app
from uchan.lib.service import page_service


@app.route('/page/<string(maxlength=20):link_name>/')
def view_page(link_name):
    page = page_service.find_page_for_link_name(link_name)
    if not page:
        abort(404)

    return render_template('page.html', page=page)
