import configparser
import json

from celery import Celery
from celery.loaders.app import AppLoader

app = None
celery = None
logger = None
mod_logger = None
configuration = None  # type: UchanConfiguration


class CustomCeleryLoader(AppLoader):
    def on_process_cleanup(self):
        from uchan.lib import database

        database.clean_up()


class UchanConfiguration():
    def __init__(self, parser):
        self.app = AppConfiguration(parser['app'])
        self.http = HttpConfiguration(parser['http'])
        self.file = FileConfiguration(parser['file'])
        self.celery = CeleryConfiguration(parser['celery'])
        self.memcache = MemcacheConfiguration(parser['memcache'])
        self.database = DatabaseConfiguration(parser['database'])


class Configuration():
    def __init__(self, section):
        self.section = section

    def get(self, name, default=None, func=None):
        if func is None:
            func = self.section.get
        value = func(name)
        if value is None:
            if default is None:
                raise Exception(name + ' not present in [' + self.section + ']')
            else:
                value = default
        return value


class AppConfiguration(Configuration):
    def __init__(self, section):
        super().__init__(section)
        self.name = self.get('name')
        self.site_url = self.get('site_url')
        self.debug = self.get('debug', func=section.getboolean, default=False)
        self.enable_cooldown_checking = self.get('enable_cooldown_checking', func=section.getboolean, default=True)
        self.bypass_worker = self.get('bypass_worker', func=section.getboolean, default=False)
        self.manifest = json.loads(self.get('manifest', default='{}'))
        self.thumbnail_op = self.get('thumbnail_op', 256)
        self.thumbnail_reply = self.get('thumbnail_reply', 128)


class HttpConfiguration(Configuration):
    def __init__(self, section):
        super().__init__(section)
        self.use_proxy_fixer = self.get('use_proxy_fixer', func=section.getboolean)
        self.proxy_fixer_num_proxies = self.get('proxy_fixer_num_proxies', func=section.getint)
        self.max_content_length = self.get('max_content_length', func=section.getint)


class FileConfiguration(Configuration):
    def __init__(self, section):
        super().__init__(section)
        self.file_cdn_type = self.get('file_cdn_type')
        self.upload_queue_path = self.get('upload_queue_path')
        self.local_cdn_path = self.get('local_cdn_path')
        self.local_cdn_web_path = self.get('local_cdn_web_path')


class CeleryConfiguration(Configuration):
    def __init__(self, section):
        super().__init__(section)
        self.broker_url = self.get('broker_url')


class MemcacheConfiguration(Configuration):
    def __init__(self, section):
        super().__init__(section)
        self.server = self.get('server')
        self.max_item_size = self.get('max_item_size', func=section.getint)


class DatabaseConfiguration(Configuration):
    def __init__(self, section):
        super().__init__(section)
        self.connect_string = self.get('connect_string')
        self.pool_size = self.get('pool_size', func=section.getint)
        self.echo = self.get('echo', default=False, func=section.getboolean)


def init():
    print('Initializing')

    global app, celery, cache, configuration

    config_parser = configparser.ConfigParser()
    config_parser.read('config.ini')
    configuration = UchanConfiguration(config_parser)

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
