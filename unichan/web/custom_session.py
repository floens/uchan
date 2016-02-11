import datetime
import json
from uuid import uuid4

from flask.sessions import SessionInterface, SessionMixin
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.datastructures import CallbackDict

from unichan.database import get_db
from unichan.lib.models import Session


class CustomSession(CallbackDict, SessionMixin):
    def __init__(self, data=None, session_id=None, new=False, force_set=False):
        def on_update(self):
            self.modified = True

        CallbackDict.__init__(self, data, on_update)
        self.session_id = session_id
        self.new = new
        self.force_set = force_set
        self.modified = False


class CustomSessionInterface(SessionInterface):
    EXPIRES_MINUTES = 2 * 60

    session_class = CustomSession

    def __init__(self, cache, prefix='session_'):
        self.cache = cache
        self.prefix = prefix

    def open_session(self, app, request):
        session_id = request.cookies.get(app.session_cookie_name)

        if not session_id:
            # No session, generate one for the client
            return self.session_class(session_id=self.generate_session_id(), new=True)
        else:
            # Session id supplied, search for it
            data = self.find_session_for_id(session_id)
            if data is not None:
                # Was a valid session id, return associated data
                return self.session_class(data=data, session_id=session_id)
            else:
                # Invalid session id, generate one
                # Force so that it will always be processed in save session, either to be deleted or set
                return self.session_class(session_id=self.generate_session_id(), new=True, force_set=True)

    def save_session(self, app, session, response):
        force = session.force_set

        # if the length is 0, thus empty
        if not session:
            # if it did contain items, delete it from the db and cookie
            # there's no point deleting a cookie when it was never saved on the client or on the server
            if (session.modified and not session.new) or force:
                self.delete_session(session.session_id)
                response.delete_cookie(app.session_cookie_name, domain=self.get_cookie_domain(app))
        elif self.should_set_cookie(app, session) or force:
            self.store_session(session.session_id, dict(session))

            if session.new or force:
                expire_date = datetime.datetime.now() + datetime.timedelta(minutes=self.EXPIRES_MINUTES)

                response.set_cookie(app.session_cookie_name, session.session_id,
                                    expires=expire_date, httponly=True, domain=self.get_cookie_domain(app))

    # Should be handled natively by flask in the future with the SESSION_REFRESH_EACH_REQUEST setting
    def should_set_cookie(self, app, session):
        return session.modified

    def generate_session_id(self):
        return str(uuid4()).replace('-', '')

    def find_session_for_id(self, session_id):
        data_json = self.cache.get(self.prefix + session_id)
        if data_json is None:
            try:
                session_model = get_db().query(Session).filter_by(session_id=session_id).one()
                data_json = session_model.data
                self.cache.set(self.prefix + session_id, data_json)
            except NoResultFound:
                return None

        if data_json is not None:
            return CustomSession(data=json.loads(data_json), session_id=session_id)
        else:
            return None

    def store_session(self, session_id, data):
        data_json = json.dumps(data)
        session_model = Session(session_id=session_id, data=data_json)

        db = get_db()
        db.add(db.merge(session_model))
        db.commit()

        self.cache.set(self.prefix + session_id, data_json)

    def delete_session(self, session_id):
        db = get_db()
        try:
            session_model = db.query(Session).filter_by(session_id=session_id).one()
            db.delete(session_model)
            db.commit()
        except NoResultFound:
            pass

        self.cache.delete(self.prefix + session_id)
