from flask import render_template, request

from uchan import app
from uchan import g
from uchan.lib.proxy_request import get_request_ip4


@app.route('/banned/')
def banned():
    g.action_authorizer.authorize_ban_check_action(request, get_request_ip4())

    bans = g.ban_service.get_request_bans()

    return render_template('banned.html', is_banned=len(bans) > 0, bans=bans)
