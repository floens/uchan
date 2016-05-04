from flask import render_template, request, url_for, redirect

from uchan import app, g
from uchan.lib import ArgumentError
from uchan.lib import BadRequestError
from uchan.lib.proxy_request import get_request_ip4
from uchan.view import check_csrf_referer


@app.route('/verify/')
def verify():
    ip4 = get_request_ip4()
    verification = g.verification_service.get_verification_for_request(request, ip4)

    method_html = ''

    verifications = []
    any_not_verified = False

    request_messages = []
    verified_messages = []

    if verification is not None:
        data = verification.data['verifications']
        for item in data:
            verifications.append(data[item])
            verified = data[item]['verified'] is True
            if not verified:
                any_not_verified = True

            message = data[item]['request_message'] if 'request_message' in data[item] else item
            if verified:
                verified_messages.append(message)
            else:
                request_messages.append(message)

    request_message = ', '.join(request_messages) if request_messages else None
    verified_message = ', '.join(verified_messages) if verified_messages else None

    if any_not_verified:
        method = g.verification_service.get_method()
        method_html = method.get_html()

    return render_template('verify.html', verifications=verifications, method_html=method_html,
                           request_message=request_message, verified_message=verified_message)


@app.route('/verify/do', methods=['POST'])
def verify_do():
    if not check_csrf_referer(request):
        raise BadRequestError('Bad referer header')

    ip4 = get_request_ip4()

    try:
        g.verification_service.do_verify(request, ip4)
    except ArgumentError as e:
        raise BadRequestError(e.message)

    return redirect(url_for('verify'))
