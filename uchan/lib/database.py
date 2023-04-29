from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from uchan import config

OrmModelBase = declarative_base()

_scoped_session = None
_session_cls = None
_engine = None


@contextmanager
def session():
    global _session_cls

    s = _session_cls()
    try:
        yield s
    except:
        s.rollback()
        raise
    finally:
        s.close()


def connect_string():
    return config.database_connect_string


def clean_up():
    global _scoped_session
    _scoped_session.remove()


def register_teardown(flask_app):
    @flask_app.teardown_appcontext
    def teardown_request(exception):
        clean_up()


# noinspection PyUnresolvedReferences
def init_db():
    """Initialize function for the database."""

    global _scoped_session
    global _session_cls
    global _engine
    global OrmModelBase

    _engine = create_engine(
        connect_string(),
        pool_size=config.database_pool_size,
        echo=config.database_echo_sql,
    )

    _session_cls = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

    _scoped_session = scoped_session(_session_cls)

    import uchan.lib.ormmodel  # noqa


def metadata_create_all():
    OrmModelBase.metadata.create_all(_engine)
