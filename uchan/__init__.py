from celery import Celery
from celery.loaders.app import AppLoader

import config


class Globals():
    def __init__(self):
        self.logger = None
        self.mod_logger = None
        self.app = None
        self.celery = None
        self.database = None
        self.plugin_manager = None

        self.cache = None
        self.posts_cache = None
        self.board_cache = None
        self.site_cache = None
        self.page_cache = None

        self.posts_service = None
        self.board_service = None
        self.moderator_service = None
        self.config_service = None
        self.file_service = None
        self.ban_service = None
        self.page_service = None
        self.verification_service = None


g = Globals()
app = None
celery = None


def setup_logger(globals):
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

    globals.logger = app.logger

    mod_log_handler = RotatingFileHandler('log/mod.log', maxBytes=5000000, backupCount=5)
    mod_log_handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))

    globals.mod_logger = logging.getLogger('mod log')
    globals.mod_logger.addHandler(mod_log_handler)
    globals.mod_logger.setLevel(logging.INFO)


class CustomCeleryLoader(AppLoader):
    def on_process_cleanup(self):
        global g
        g.database.clean_up()


def init():
    print('Initializing')

    global g, app, celery
    assert isinstance(g, Globals)

    import uchan.lib.database as database
    g.database = database
    database.init_db()

    celery = g.celery = Celery('uchan', loader=CustomCeleryLoader)
    g.celery.config_from_object('config_celery')

    # Import it here so that the templates resolve correctly
    from uchan.web import create_web_app, CustomFlaskApp
    app = g.app = CustomFlaskApp(__name__)
    create_web_app(g, config, g.app)

    database.register_teardown(g.app)

    from uchan.lib.cache import CacheWrapper
    g.cache = CacheWrapper(servers=config.MEMCACHED_SERVERS)

    # Setup session handling
    from uchan.web.custom_session import CustomSessionInterface
    app.session_interface = CustomSessionInterface(g.cache)

    # Import views
    import uchan.view

    # Import jinja filters
    import uchan.filter.app_filters

    # Import blueprints
    from uchan.mod import mod
    app.register_blueprint(mod)

    from uchan.api import api
    app.register_blueprint(api)

    setup_logger(g)

    from uchan.lib.plugin_manager import PluginManager
    g.plugin_manager = PluginManager()

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
    g.moderator_service = ModeratorService()

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

    from uchan.lib.service import PageService
    from uchan.lib.cache import PageCache
    g.page_service = PageService()
    g.page_cache = PageCache(g.cache)

    from uchan.lib.service import VerificationService
    g.verification_service = VerificationService(g.cache)

    # print('Loading plugins')

    import uchan.plugins
    g.plugin_manager.load_plugins(config.PLUGINS)

    print('Done')


init()
