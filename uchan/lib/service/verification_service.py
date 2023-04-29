import datetime
from uuid import uuid4

from flask import Request
from flask import g as flaskg

from uchan.lib.model import VerificationsModel
from uchan.lib.proxy_request import get_request_ip4
from uchan.lib.repository import verifications
from uchan.lib.repository.verifications import VerifyingClient

VERIFICATION_COOKIE_NAME = "verification"

from uchan import app  # noqa
from uchan.lib.cache import CacheDict  # noqa
from uchan.lib.utils import get_cookie_domain  # noqa


class VerificationMethod:
    def get_html(self):
        raise NotImplementedError()

    def get_javascript(self):
        raise NotImplementedError()

    def verification_in_request(self, request):
        raise NotImplementedError()

    def verify_request(self, request):
        raise NotImplementedError()


class VerificationDataCache(CacheDict):
    def __init__(self, ip4, expires, data):
        super().__init__()
        self.ip4 = ip4
        self.expires = expires
        self.data = data


methods = []

"""
This verification service is separate from the normal session cookie so that it can
easily be managed with varnish. The verification should never change GET requests except
for /verify/. Verifications are also bound to an ip4 address to avoid sharing
verifications with multiple users.

Endpoints can check verification with the require_verification decorator.
"""


def add_method(method: VerificationMethod):
    methods.append(method)


def get_method() -> VerificationMethod:
    if not methods:
        raise Exception("No verification methods configured")

    return methods[0]


def is_verified(request: Request) -> bool:
    client = _get_client(request)
    if not client:
        return False

    verified = verifications.is_verified(client)

    return verified


def set_verified(request: Request):
    client = _create_client(request)

    verification: VerificationsModel = verifications.set_verified(client)

    # Flushes the cookie, see function below
    flaskg.pending_verification = verification


# Called after the request to attach the set-cookie to the response
def after_request(response):
    if hasattr(flaskg, "pending_verification"):
        verification: VerificationsModel = flaskg.pending_verification

        name = VERIFICATION_COOKIE_NAME
        value = verification.id
        expire_date = datetime.datetime.utcfromtimestamp(verification.expires / 1000)
        domain = get_cookie_domain(app)

        response.set_cookie(
            name, value, expires=expire_date, httponly=True, domain=domain
        )


def _get_client(request: Request):
    verification_id = (
        request.cookies[VERIFICATION_COOKIE_NAME]
        if VERIFICATION_COOKIE_NAME in request.cookies
        else None
    )
    if not verification_id:
        return None

    ip4 = get_request_ip4(request)

    return VerifyingClient.from_verification_id_ip4(verification_id, ip4)


def _create_client(request: Request):
    verification_id = _generate_verification_id()
    ip4 = get_request_ip4(request)

    return VerifyingClient.from_verification_id_ip4(verification_id, ip4)


def _generate_verification_id():
    return str(uuid4()).replace("-", "")
