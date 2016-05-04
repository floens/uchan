import datetime
from uuid import uuid4

from flask.sessions import SessionInterface, SessionMixin
from sqlalchemy.orm.exc import NoResultFound
from uchan.lib.cache import CacheDict
from uchan.lib.database import get_db
from uchan.lib.models import Session
from uchan.lib.utils import now
from werkzeug.datastructures import CallbackDict


class CustomSession(CallbackDict, SessionMixin):
    def __init__(self, initial=None, session_id=None, new=False, was_invalid=False, expires=0):
        def on_update(self):
            self.modified = True

        CallbackDict.__init__(self, initial, on_update)
        self.session_id = session_id
        self.expires = expires
        self.new = new
        self.was_invalid = was_invalid
        self.modified = False


class CustomSessionCacheDict(CacheDict):
    def __init__(self, data, expires):
        super().__init__(self)
        self.data = data
        self.expires = expires


class CustomSessionInterface(SessionInterface):
    EXPIRES_MINUTES = 2 * 60

    session_class = CustomSession

    def __init__(self, cache, prefix='session$'):
        self.cache = cache
        self.prefix = prefix

    def open_session(self, app, request):
        session_id = request.cookies.get(app.session_cookie_name)

        expires = int(now() + 1000 * datetime.timedelta(minutes=self.EXPIRES_MINUTES).total_seconds())
        if not session_id:
            # No session, generate one for the client
            return self.session_class(session_id=self.generate_session_id(), new=True, expires=expires)
        else:
            # Session id supplied, search for it in storage
            session = self.find_session_for_id(session_id)
            if session is not None:
                # Was a valid session id, check data
                if now() < session.expires:
                    return self.session_class(initial=session, session_id=session.session_id, expires=session.expires)

        # Invalid session id or expired, generate a new one
        # Force so that it will always be processed in save session, either to be deleted or set
        return self.session_class(session_id=self.generate_session_id(), new=True, was_invalid=True, expires=expires)

    def save_session(self, app, session, response):
        # Reset the state when the client supplied an invalid or expired cookie
        # Either by an expired cookie or an invalid cookie
        if session.was_invalid:
            # if the length is 0, thus empty
            if not session:
                # It just deletes the cookie from the client
                # Was invalid is only for new sessions, so no db and cache synching needed
                self.delete_cookie(app, session, response)
            else:
                # Otherwise if it now contains data sync it to the client, db and cache
                self.store_session_db(session)
                self.store_session_cache(session)
                self.store_cookie(app, session, response)
        else:
            # if the length is 0, thus empty
            if not session:
                # if it did contain items, delete it from the db and cookie
                # there's no point deleting a cookie when it was never saved on the client or on the server
                if not session.new and session.modified:
                    self.delete_session(session.session_id)
                    self.delete_cookie(app, session, response)
            # If it was modified and not empty now
            elif self.should_set_cookie(app, session):
                # Update the db and cache with the new contents
                self.store_session_db(session)
                self.store_session_cache(session)

                # Sync to the client if new
                if session.new:
                    self.store_cookie(app, session, response)

    # Should be handled natively by flask in the future with the SESSION_REFRESH_EACH_REQUEST setting
    def should_set_cookie(self, app, session):
        return session.modified

    def generate_session_id(self):
        return str(uuid4()).replace('-', '')

    def find_session_for_id(self, session_id):
        cache_data = self.cache.get(self.prefix + session_id, True)
        if cache_data is not None:
            return CustomSession(initial=cache_data.data, session_id=session_id, expires=cache_data.expires)
        else:
            try:
                session_model = get_db().query(Session).filter_by(session_id=session_id).one()

                session = CustomSession(initial=session_model.data,
                                        session_id=session_id, expires=session_model.expires)

                self.store_session_cache(session)

                return session
            except NoResultFound:
                return None

    def store_cookie(self, app, session, response):
        # expire_date = datetime.datetime.now() + datetime.timedelta(minutes=self.EXPIRES_MINUTES)
        expire_date = datetime.datetime.utcfromtimestamp(session.expires / 1000)
        response.set_cookie(app.session_cookie_name, session.session_id,
                            expires=expire_date, httponly=True, domain=self.get_cookie_domain(app))

    def delete_cookie(self, app, session, response):
        response.delete_cookie(app.session_cookie_name, domain=self.get_cookie_domain(app))

    def store_session_db(self, session):
        session_model = Session(session_id=session.session_id, data=session, expires=session.expires)

        db = get_db()
        db.add(db.merge(session_model))
        db.commit()

    def store_session_cache(self, session):
        self.cache.set(self.prefix + session.session_id, CustomSessionCacheDict(session, session.expires))

    def delete_session(self, session_id):
        db = get_db()
        try:
            session_model = db.query(Session).filter_by(session_id=session_id).one()
            db.delete(session_model)
            db.commit()
        except NoResultFound:
            pass

        self.cache.delete(self.prefix + session_id)
