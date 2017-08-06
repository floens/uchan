from flask import render_template, request

from uchan import app
from uchan.lib.service import ban_service, verification_service
from uchan.lib.exceptions import BadRequestError, ArgumentError
from uchan.lib.utils import now


# Do NOT cache this GET endpoint, an exception in the varnish config has been made.
@app.route('/banned/', methods=['GET', 'POST'])
def banned():
    method = verification_service.get_method()
    if request.method == 'GET':
        return render_template('banned.html', method=method)
    else:
        try:
            method.verify_request(request)
        except ArgumentError as e:
            raise BadRequestError(e.message)

        bans = ban_service.get_request_bans(True)

        return render_template('banned.html', is_banned=len(bans) > 0, bans=bans, now=now)
