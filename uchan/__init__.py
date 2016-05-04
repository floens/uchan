import config
from celery import Celery
from celery.loaders.app import AppLoader


class Globals:
    def __init__(self):
        self._logger = None
        self._mod_logger = None
        self._app = None
        self._celery = None
        self._database = None
        self._plugin_manager = None
        self._action_authorizer = None

        self._cache = None
        self._posts_cache = None
        self._board_cache = None
        self._site_cache = None
        self._page_cache = None

        self._posts_service = None
        self._board_service = None
        self._moderator_service = None
        self._config_service = None
        self._file_service = None
        self._ban_service = None
        self._page_service = None
        self._verification_service = None
        self._report_service = None

    @property
    def logger(self):
        return self._logger

    @property
    def mod_logger(self):
        return self._mod_logger

    @property
    def app(self):
        return self._app

    @property
    def celery(self):
        return self._celery

    @property
    def database(self):
        return self._database

    @property
    def plugin_manager(self):
        return self._plugin_manager

    @property
    def action_authorizer(self):
        return self._action_authorizer

    @property
    def cache(self):
        return self._cache

    @property
    def posts_cache(self):
        return self._posts_cache

    @property
    def board_cache(self):
        return self._board_cache

    @property
    def site_cache(self):
        return self._site_cache

    @property
    def page_cache(self):
        return self._page_cache

    @property
    def posts_service(self):
        return self._posts_service

    @property
    def board_service(self):
        return self._board_service

    @property
    def moderator_service(self):
        return self._moderator_service

    @property
    def config_service(self):
        return self._config_service

    @property
    def file_service(self):
        return self._file_service

    @property
    def ban_service(self):
        return self._ban_service

    @property
    def page_service(self):
        return self._page_service

    @property
    def verification_service(self):
        return self._verification_service

    @property
    def report_service(self):
        return self._report_service


g = Globals()  # Type: Globals
app = None
celery = None


def setup_logger(g):
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

    g._logger = app.logger

    mod_log_handler = RotatingFileHandler('log/mod.log', maxBytes=5000000, backupCount=5)
    mod_log_handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))

    g._mod_logger = logging.getLogger('mod log')
    g._mod_logger.addHandler(mod_log_handler)
    g._mod_logger.setLevel(logging.INFO)


class CustomCeleryLoader(AppLoader):
    def on_process_cleanup(self):
        global g
        g.database.clean_up()


def init():
    print('Initializing')

    global g, app, celery

    import uchan.lib.database as database
    database.init_db()
    g._database = database

    celery = g._celery = Celery('uchan', loader=CustomCeleryLoader)
    g._celery.config_from_object('config_celery')

    # Import it here so that the templates resolve correctly
    from uchan.web import create_web_app, CustomFlaskApp
    app = g._app = CustomFlaskApp(__name__)
    create_web_app(g, config, g.app)

    database.register_teardown(g.app)

    from uchan.lib.cache import CacheWrapper
    g._cache = CacheWrapper(servers=config.MEMCACHED_SERVERS)

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

    from uchan.lib.action_authorizer import ActionAuthorizer
    g._action_authorizer = ActionAuthorizer()

    from uchan.lib.plugin_manager import PluginManager
    g._plugin_manager = PluginManager()

    # Setup singletons
    from uchan.lib.service import PostsService
    from uchan.lib.cache import PostsCache
    g._posts_cache = PostsCache(g.cache)
    g._posts_service = PostsService()

    from uchan.lib.service import BoardService
    from uchan.lib.cache import BoardCache
    g._board_cache = BoardCache(g.cache)
    g._board_service = BoardService()

    from uchan.lib.service import ModeratorService
    g._moderator_service = ModeratorService()

    from uchan.lib.service import ReportService
    g._report_service = ReportService()

    from uchan.lib.service import ConfigService
    g._config_service = ConfigService()

    from uchan.lib.cache import SiteCache
    g._site_cache = SiteCache(g.cache)

    from uchan.lib.service import FileService, LocalCdn

    if config.FILE_CDN_TYPE == 'local':
        cdn = LocalCdn(config.LOCAL_CDN_PATH, config.LOCAL_CDN_WEB_PATH)
    else:
        raise Exception('Unknown file cdn type')

    g._file_service = FileService(config.UPLOAD_QUEUE_PATH, cdn)

    from uchan.lib.service import BanService
    g._ban_service = BanService()

    from uchan.lib.service import PageService
    from uchan.lib.cache import PageCache
    g._page_service = PageService()
    g._page_cache = PageCache(g.cache)

    from uchan.lib.service import VerificationService
    g._verification_service = VerificationService(g.cache)

    # print('Loading plugins')

    import uchan.plugins
    g._plugin_manager.load_plugins(config.PLUGINS)

    # database.metadata_create_all()

    print('Done')


init()
