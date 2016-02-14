from flask import render_template

from unichan import app
from unichan import g


@app.route('/banned/')
def banned():
    bans = g.ban_service.get_request_bans()

    return render_template('banned.html', is_banned=len(bans) > 0, bans=bans)
