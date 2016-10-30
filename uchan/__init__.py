from celery import Celery
from celery.loaders.app import AppLoader

import config

app = None
celery = None
logger = None
mod_logger = None


class CustomCeleryLoader(AppLoader):
    def on_process_cleanup(self):
        from uchan.lib import database

        database.clean_up()


def init():
    print('Initializing')

    global app, celery, cache

    import uchan.lib.database as database
    database.init_db()

    celery = Celery('uchan', loader=CustomCeleryLoader)
    celery.config_from_object('config_celery')

    # Import it here so that the templates resolve correctly
    from uchan.web import create_web_app, CustomFlaskApp
    app = CustomFlaskApp(__name__)
    setup_logging()
    create_web_app(config, app)

    database.register_teardown(app)

    from uchan.lib.cache import CacheWrapper
    cache = CacheWrapper(servers=config.MEMCACHED_SERVERS)

    # Setup session handling
    from uchan.web.custom_session import CustomSessionInterface
    app.session_interface = CustomSessionInterface(cache)

    # Import views
    import uchan.view

    # Import jinja filters
    import uchan.filter.app_filters

    # Import blueprints
    from uchan.mod import mod
    app.register_blueprint(mod)

    from uchan.api import api
    app.register_blueprint(api)

    from uchan.lib.service.file_service import LocalCdn

    if config.FILE_CDN_TYPE == 'local':
        cdn = LocalCdn(config.LOCAL_CDN_PATH, config.LOCAL_CDN_WEB_PATH)
    else:
        raise Exception('Unknown file cdn type')

    from uchan.lib.service import file_service
    file_service.cdn = cdn
    file_service.upload_queue_path = config.UPLOAD_QUEUE_PATH

    # print('Loading plugins')

    from uchan.lib import plugin_manager
    plugin_manager.load_plugins(config.PLUGINS)

    # database.metadata_create_all()

    print('Done')


def setup_logging():
    global app, logger, mod_logger

    import config
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

    mod_log_handler = RotatingFileHandler('log/mod.log', maxBytes=5000000, backupCount=5)
    mod_log_handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))

    mod_logger = logging.getLogger('mod log')
    mod_logger.addHandler(mod_log_handler)
    mod_logger.setLevel(logging.INFO)


init()
