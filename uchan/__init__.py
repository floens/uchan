from celery import Celery
from celery.loaders.app import AppLoader
from flask import Flask, render_template
from werkzeug.contrib.fixers import ProxyFix

import config
from uchan.database import clean_up
from uchan.web import CustomSessionInterface


class Globals():
    def __init__(self):
        self.logger = None
        self.app = None
        self.celery = None
        self.database = None

        self.cache = None
        self.posts_cache = None
        self.board_cache = None
        self.site_cache = None
        self.posts_service = None
        self.board_service = None
        self.moderator_service = None
        self.config_service = None
        self.file_service = None
        self.ban_service = None


g = Globals()
app = None
celery = None


class CustomFlaskApp(Flask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def reset_sessions(self, db, session_ids_to_skip):
        from uchan.lib.models import Session

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
    if config.USE_PROXY_FIXER:
        app.wsgi_app = ProxyFix(app.wsgi_app, config.PROXY_FIXER_NUM_PROXIES)

    app.config.from_object('config')

    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True

    from uchan.lib import BadRequestError

    # Setup error handlers
    def bad_request(e):
        if isinstance(e, BadRequestError):
            while isinstance(e, Exception) and len(e.args) > 0:
                e = e.args[0]

        return e if type(e) is str else ''

    @app.errorhandler(500)
    def server_error_handler(error):
        g.logger.exception(error)
        return app.send_static_file('500.html'), 500

    @app.errorhandler(404)
    def server_error_handler(error):
        g.logger.exception(error)
        return app.send_static_file('404.html'), 404

    @app.errorhandler(BadRequestError)
    def bad_request_handler(error):
        return render_template('error.html', message=bad_request(error)), 400

    # Setup session handling
    app.session_interface = CustomSessionInterface(cache)

    return app


class CustomCeleryLoader(AppLoader):
    def on_process_cleanup(self):
        global g
        g.database.clean_up()


def init():
    global g, app, celery
    assert isinstance(g, Globals)

    from uchan.lib.cache import CacheWrapper
    g.cache = CacheWrapper(servers=config.MEMCACHED_SERVERS)

    import uchan.database as database
    g.database = database
    database.init_db()

    celery = g.celery = Celery('uchan', loader=CustomCeleryLoader)
    g.celery.config_from_object('config_celery')

    # Import it here so that the templates resolve correctly
    app = g.app = CustomFlaskApp(__name__)
    create_web_app(g.app, g.cache)
    database.register_teardown(g.app)

    # Import views here
    import uchan.view.index
    import uchan.view.board
    import uchan.view.post
    import uchan.view.thread
    import uchan.view.banned

    # Import jinja filters
    import uchan.filter.app_filters

    # Import blueprints
    from uchan.mod import mod
    app.register_blueprint(mod)

    from uchan.api import api
    app.register_blueprint(api)

    g.logger = setup_logger()

    # Setup singletons
    from uchan.lib.service import PostsService
    from uchan.lib.cache import PostsCache
    g.posts_cache = PostsCache(g.cache)
    g.posts_service = PostsService()

    from uchan.lib.service import BoardService
    from uchan.lib.cache import BoardCache
    g.board_cache = BoardCache(g.cache)
    g.board_service = BoardService()

    from uchan.lib.service import ModeratorService
    g.moderator_service = ModeratorService(g.cache)

    from uchan.lib.service import ConfigService
    g.config_service = ConfigService()

    from uchan.lib.cache import SiteCache
    g.site_cache = SiteCache(g.cache)

    from uchan.lib.service import FileService, LocalCdn

    if config.FILE_CDN_TYPE == 'local':
        cdn = LocalCdn(config.LOCAL_CDN_PATH, config.LOCAL_CDN_WEB_PATH)
    else:
        raise Exception('Unknown file cdn type')

    g.file_service = FileService(config.UPLOAD_QUEUE_PATH, cdn)

    from uchan.lib.service import BanService
    g.ban_service = BanService()


init()
