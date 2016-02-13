from flask import render_template

from unichan.database import get_db
from unichan.lib.models import Report
from unichan.mod import mod


@mod.route('/mod_post')
def mod_post():
    reports = get_db().query(Report).all()

    return render_template('mod_post.html', reports=reports)
