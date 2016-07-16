import datetime
from uuid import uuid4

from flask import g as flaskg
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm.exc import NoResultFound
from uchan import g
from uchan.lib.cache import CacheDict
from uchan.lib.database import get_db
from uchan.lib.models import Verification
from uchan.lib.utils import now, get_cookie_domain


class VerificationMethod:
    def get_html(self):
        raise NotImplementedError()

    def verify_request(self, request):
        raise NotImplementedError()


class VerificationDataCache(CacheDict):
    def __init__(self, ip4, expires, data):
        super().__init__()
        self.ip4 = ip4
        self.expires = expires
        self.data = data


class VerificationService:
    """
    This verification service is seperate from the normal session cookie so that it can easily be
    managed with varnish. The verification should never change GET requests except for /verify/.
    Verifications are also bound to an ip4 address to avoid sharing verifications with multiple users.

    Endpoints can check verification with the require_verification decorator.
    """
    VERIFICATION_COOKIE_NAME = 'verification'
    COOKIE_DURATION = 1000 * 60 * 60 * 24

    def __init__(self, cache):
        self.cache = cache

        self.methods = []

    def add_method(self, method):
        self.methods.append(method)

    def get_method(self):
        if not self.methods:
            raise Exception('No verification methods configured')

        return self.methods[0]

    def handle_not_verified(self, verification_error, request, ip4):
        name = verification_error.for_name
        message = verification_error.request_message
        single_shot = verification_error.single_shot

        self.set_verification(request, ip4, name, False, request_message=message, single_shot=single_shot)

    def process_request(self, request, ip4, name):
        verification_data = g.verification_service.get_verification_data_for_request(request, ip4, name)
        if verification_data is None:
            return False

        ret = verification_data['verified'] is True
        if 'single_shot' in verification_data and verification_data['single_shot']:
            # Update verified to false again, not changing the other options
            self.set_verification(request, ip4, name, False)
        return ret

    def data_is_verified(self, verification_data):
        if verification_data is None:
            return False
        return verification_data['verified'] is True

    def get_verification_data_for_request(self, request, ip4, name):
        verification = self.get_verification_for_request(request, ip4)
        if verification is not None:
            if name in verification.data['verifications']:
                return verification.data['verifications'][name]
        return None

    def do_verify(self, request, ip4):
        method = self.get_method()
        method.verify_request(request)

        verification = self.get_verification_for_request(request, ip4, with_cache=False)
        if verification is not None:
            db = get_db()
            for item in verification.data['verifications']:
                verification.data['verifications'][item]['verified'] = True
            # Force a db refresh
            flag_modified(verification, 'data')
            db.commit()
            self.invalidate_cache(verification, now())

        return verification

    def set_verification(self, request, ip4, name, verified, request_message=None, single_shot=None, extra_data=None):
        verification = self.get_verification_for_request(request, ip4, with_cache=False)

        db = get_db()

        if verification is None:
            verification = Verification()
            verification.verification_id = self.generate_verification_id()
            db.add(verification)

        time = now()

        verification.expires = time + self.COOKIE_DURATION
        verification.ip4 = ip4

        if verification.data is None:
            verification.data = {
                'verifications': {}
            }

        data = verification.data['verifications']
        if name not in data:
            data[name] = {}

        data[name]['verified'] = verified
        if request_message:
            data[name]['request_message'] = request_message

        if single_shot is not None:
            data[name]['single_shot'] = bool(single_shot)

        if extra_data is not None:
            for item in extra_data:
                data[name][item] = extra_data[item]

        # Force a db refresh
        flag_modified(verification, 'data')

        db.commit()

        self.invalidate_cache(verification, time)

        flaskg.pending_verification = verification

        return verification

    def get_verification_for_request(self, request, ip4, with_cache=True):
        verification_id = self.get_verification_id_from_request(request)
        if not verification_id:
            return None

        time = now()

        if with_cache:
            verification_data_cache = self.cache.get(self.get_verified_cache_key(verification_id), True)
            if not verification_data_cache:
                return None

            if verification_data_cache.ip4 == ip4 and verification_data_cache.expires > 0 and time < verification_data_cache.expires:
                return verification_data_cache

        verification = self.find_verification_id(verification_id)
        if not verification:
            return None

        if verification.ip4 == ip4 and verification.expires > 0 and time < verification.expires:
            return verification

        return None

    def get_verified_cache_key(self, verification_id):
        return 'verification${}'.format(verification_id)

    def invalidate_cache(self, verification, time):
        # timeout in seconds
        cachetimeout = max(1, (verification.expires - time) // 1000)
        cache_data = VerificationDataCache(verification.ip4, verification.expires, verification.data)
        self.cache.set(self.get_verified_cache_key(verification.verification_id), cache_data, timeout=cachetimeout)

    def get_verification_id_from_request(self, request):
        if self.VERIFICATION_COOKIE_NAME not in request.cookies:
            return None

        return request.cookies[self.VERIFICATION_COOKIE_NAME]

    def find_verification_id(self, verification_id):
        db = get_db()
        try:
            return db.query(Verification).filter_by(verification_id=verification_id).one()
        except NoResultFound:
            return None

    def after_request(self, response):
        if hasattr(flaskg, 'pending_verification'):
            verification = flaskg.pending_verification
            expire_date = datetime.datetime.utcfromtimestamp(verification.expires / 1000)
            response.set_cookie('verification', verification.verification_id, expires=expire_date, httponly=True,
                                domain=get_cookie_domain(g.app))

    def generate_verification_id(self):
        return str(uuid4()).replace('-', '')
