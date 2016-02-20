from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

import config

ModelBase = declarative_base()

_sessionconstruct = None
_engine = None


def get_db():
    global _sessionconstruct

    return _sessionconstruct()


def connect_string():
    return config.DATABASE_CONNECT_STRING


def clean_up():
    global _sessionconstruct
    _sessionconstruct.remove()


def register_teardown(flask_app):
    @flask_app.teardown_appcontext
    def teardown_request(exception):
        clean_up()


# noinspection PyUnresolvedReferences
def init_db():
    """Initialize function for the database.
    """

    global _sessionconstruct
    global _engine
    global ModelBase

    _engine = create_engine(connect_string(), pool_size=config.DATABASE_POOL_SIZE)
    _sessionconstruct = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=_engine))

    # Import our models. If you add new models, import them here.
    from unichan.lib.models import Post, Thread, Board, Session, Report, Moderator, Config, File, Ban


def metadata_create_all():
    ModelBase.metadata.create_all(_engine)
