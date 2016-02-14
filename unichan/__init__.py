from celery import Celery
from celery.loaders.app import AppLoader
from flask import Flask, render_template

import config
from unichan.database import clean_up
from unichan.lib import BadRequestError
from unichan.web import CustomSessionInterface


class Globals():
    def __init__(self):
        self.logger = None
        self.app = None
        self.celery = None
        self.database = None

        self.memcached_cache = None
        self.cache = None
        self.posts_cache = None
        self.board_cache = None
        self.site_cache = None
        self.posts_service = None
        self.board_service = None
        self.moderator_service = None
        self.config_service = None
        self.file_service = None


g = Globals()
app = None
celery = None


class CustomFlaskApp(Flask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def reset_sessions(self, db, session_ids_to_skip):
        from unichan.lib.models import Session

        all_sessions = db.query(Session).all()
        for session_item in all_sessions:
            if session_item.session_id not in session_ids_to_skip:
                self.session_interface.delete_session(session_item.session_id)


def setup_logger():
    import config

    global app

    # Setup logging
    import logging
    from logging.handlers import RotatingFileHandler

    app.logger.handlers[0].setFormatter(
            logging.Formatter("[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s"))
    log_handler = RotatingFileHandler('log/' + config.APP_NAME + '.log', maxBytes=5000000, backupCount=5)
    log_handler.setFormatter(logging.Formatter("[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s"))
    app.logger.addHandler(log_handler)
    if config.DEBUG:
        log_handler.setLevel(logging.DEBUG)
        app.logger.setLevel(logging.DEBUG)
    else:
        log_handler.setLevel(logging.INFO)
        app.logger.setLevel(logging.INFO)

    logger = app.logger
    return logger


def create_web_app(app, cache):
    app.config.from_object('config')

    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True

    # Setup error handlers
    def bad_request(e):
        if isinstance(e, BadRequestError):
            while isinstance(e, Exception) and len(e.args) > 0:
                e = e.args[0]

        return e if type(e) is str else ''

    @app.errorhandler(BadRequestError)
    def bad_request_handler(error):
        return render_template('error.html', message=bad_request(error))

    # Setup session handling
    app.session_interface = CustomSessionInterface(cache)

    return app


class CustomCeleryLoader(AppLoader):
    def on_process_cleanup(self):
        global g
        g.database.clean_up()


def init():
    global g, app, celery

    from werkzeug.contrib.cache import MemcachedCache
    from unichan.lib.cache import CacheWrapper
    g.memcached_cache = MemcachedCache()
    g.cache = CacheWrapper(g.memcached_cache)

    import unichan.database as database
    g.database = database
    database.init_db()

    celery = g.celery = Celery('unichan', loader=CustomCeleryLoader)
    g.celery.config_from_object('config_celery')

    # Import it here so that the templates resolve correctly
    app = g.app = CustomFlaskApp(__name__)
    create_web_app(g.app, g.cache)
    database.register_teardown(g.app)

    # Import views here
    import unichan.view.index
    import unichan.view.board
    import unichan.view.post
    import unichan.view.thread

    # Import jinja filters
    import unichan.filter.app_filters

    # Import blueprints
    from unichan.mod import mod
    app.register_blueprint(mod)

    from unichan.api import api
    app.register_blueprint(api)

    g.logger = setup_logger()

    # Setup singletons
    from unichan.lib.service import PostsService
    from unichan.lib.cache import PostsCache
    g.posts_cache = PostsCache(g.cache)
    g.posts_service = PostsService()

    from unichan.lib.service import BoardService
    from unichan.lib.cache import BoardCache
    g.board_cache = BoardCache(g.cache)
    g.board_service = BoardService()

    from unichan.lib.service import ModeratorService
    g.moderator_service = ModeratorService(g.cache)

    from unichan.lib.service import ConfigService
    g.config_service = ConfigService()

    from unichan.lib.cache import SiteCache
    g.site_cache = SiteCache(g.cache)

    from unichan.lib.service import FileService, LocalCdn

    if config.FILE_CDN_TYPE == 'local':
        cdn = LocalCdn(config.LOCAL_CDN_PATH, config.LOCAL_CDN_WEB_PATH)
    else:
        raise Exception('Unknown file cdn type')

    g.file_service = FileService(config.UPLOAD_QUEUE_PATH, cdn)

    # database.metadata_create_all()
    # test_models()


def test_models():
    try:
        from unichan import g

        from unichan.lib.configs import BoardConfig, SiteConfig

        if g.config_service.get_config_by_type(SiteConfig.TYPE) is None:
            g.config_service.save_config(SiteConfig(), None)

        from unichan.lib.models import Board
        b_board = g.board_service.find_board('b')
        if not b_board:
            a_board = Board()
            a_board.name = 'a'
            g.board_service.add_board(a_board)

            b_board = Board()
            b_board.name = 'b'
            g.board_service.add_board(b_board)

        from unichan.lib import roles
        from unichan.lib.models import Moderator

        existing_moderator = g.moderator_service.find_moderator_username('florens')
        if not existing_moderator:
            moderator = Moderator()
            moderator.roles = [roles.ROLE_ADMIN]
            moderator.username = 'florens'

            g.moderator_service.create_moderator(moderator, 'passwd')
    finally:
        clean_up()


init()
