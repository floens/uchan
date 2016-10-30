from flask import render_template, request

from uchan import app
from uchan.lib.service import ban_service, verification_service
from uchan.lib import BadRequestError, ArgumentError
from uchan.lib.utils import now


@app.route('/banned/', methods=['GET', 'POST'])
def banned():
    if request.method == 'GET':
        method = verification_service.get_method()
        method_html = method.get_html()

        return render_template('banned.html', method_html=method_html)
    else:
        method = verification_service.get_method()
        try:
            method.verify_request(request)
        except ArgumentError as e:
            raise BadRequestError(e.message)

        bans = ban_service.get_request_bans()

        return render_template('banned.html', is_banned=len(bans) > 0, bans=bans, now=now)
