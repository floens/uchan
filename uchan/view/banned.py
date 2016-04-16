from flask import render_template, url_for

from uchan import app
from uchan import g
from uchan.view import require_verification


@app.route('/banned/')
@require_verification('ban_check', 'Verify here before checking your ban', 'ban checking')
def banned():
    bans = g.ban_service.get_request_bans()

    return render_template('banned.html', is_banned=len(bans) > 0, bans=bans)
