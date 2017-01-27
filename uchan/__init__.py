import configparser

from celery import Celery
from celery.loaders.app import AppLoader

app = None
celery = None
logger = None
mod_logger = None
configuration = None  # type: uchan.config.UchanConfiguration


class CustomCeleryLoader(AppLoader):
    def on_process_cleanup(self):
        from uchan.lib import database

        database.clean_up()


import uchan.config


def init():
    print('Initializing')

    global app, celery, cache, configuration

    config_parser = configparser.ConfigParser()
    config_parser.read('config.ini')
    configuration = config.UchanConfiguration(config_parser)

    import uchan.lib.database as database
    database.init_db()

    celery = Celery('uchan', loader=CustomCeleryLoader)
    celery.config_from_object({
        'CELERY_RESULT_BACKEND': 'rpc://',
        'CELERY_TASK_SERIALIZER': 'pickle',
        'CELERY_ACCEPT_CONTENT': ['pickle'],
        'CELERY_RESULT_SERIALIZER': 'pickle',
        'BROKER_URL': configuration.celery.broker_url
    })

    # Import it here so that the templates resolve correctly
    from uchan.web import create_web_app, CustomFlaskApp
    app = CustomFlaskApp(__name__)
    setup_logging()
    create_web_app(configuration, app)

    database.register_teardown(app)

    from uchan.lib.cache import cache

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

    if configuration.file.file_cdn_type == 'local':
        cdn = LocalCdn(configuration.file.local_cdn_path, configuration.file.local_cdn_web_path)
    else:
        raise Exception('Unknown file cdn type')

    from uchan.lib.service import file_service
    file_service.init(configuration.file.upload_queue_path, cdn)

    # Register tasks
    import uchan.lib.tasks

    # print('Loading plugins')

    from uchan.lib import plugin_manager

    plugins = list(map(str.strip, config_parser['plugins']['plugins'].split(',')))
    plugin_manager.load_plugins(plugins, config_parser)

    # database.metadata_create_all()

    print('Done')


def setup_logging():
    global app, logger, mod_logger

    import logging
    from logging.handlers import RotatingFileHandler

    app.logger.handlers[0].setFormatter(
        logging.Formatter("[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s"))
    log_handler = RotatingFileHandler('log/' + configuration.app.name + '.log', maxBytes=5000000, backupCount=5)
    log_handler.setFormatter(logging.Formatter("[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s"))
    app.logger.addHandler(log_handler)
    if configuration.app.debug:
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
