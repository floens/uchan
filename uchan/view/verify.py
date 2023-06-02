from flask import render_template, request

from uchan import app
from uchan.lib.exceptions import ArgumentError, BadRequestError
from uchan.lib.service import verification_service
from uchan.view import check_csrf_referer, with_cache_control_no_store


# Do NOT cache this GET endpoint, an exception in the varnish config has been made.
@app.route("/verify/", methods=["GET", "POST"])
@with_cache_control_no_store()
def verify():
    method = verification_service.get_method()
    verified = False
    verified_message = None

    if request.method == "POST":
        if not check_csrf_referer(request):
            raise BadRequestError("Bad referer header")

        if verification_service.is_verified(request):
            verified = True
        elif method.verification_in_request(request):
            try:
                method.verify_request(request)
                verification_service.set_verified(request)
                verified = True
            except ArgumentError as e:
                verified_message = e.message
    else:
        verified = verification_service.is_verified(request)

    return render_template(
        "verify.html",
        method=method,
        verified=verified,
        verified_message=verified_message,
    )
