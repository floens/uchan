from flask import abort, render_template

from uchan import app
from uchan.lib.service import page_service


@app.route("/")
def index():
    page = page_service.find_front_page()
    if not page:
        abort(404)

    return render_template("index.html", page=page)
