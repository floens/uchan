import configparser
import os
import sys

from celery import Celery
from celery.loaders.app import AppLoader
from flask_assets import Environment
from webassets import Bundle

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
    global app, celery, cache, configuration

    config_file = 'config.ini'
    if 'UCHAN_CONFIG_FILE' in os.environ:
        config_file = os.environ['UCHAN_CONFIG_FILE']

    config_parser = configparser.ConfigParser()
    if not config_parser.read(config_file):
        print('Error reading config.ini. Please copy config.ini.sample to config.ini and adjust accordingly.')
        sys.exit(1)
    configuration = config.UchanConfiguration(config_parser)

    import uchan.lib.database as database
    database.init_db()

    celery = Celery('uchan', loader=CustomCeleryLoader)
    celery.config_from_object({
        'result_backend': 'rpc://',
        'task_serializer': 'pickle',
        'accept_content': ['pickle'],
        'result_serializer': 'pickle',
        'broker_url': configuration.celery.broker_url
    })

    # Import it here so that the templates resolve correctly
    from uchan.flask import create_web_app, CustomFlaskApp
    app = CustomFlaskApp(__name__, template_folder='view/templates', static_folder='view/static')
    setup_logging()
    create_web_app(configuration, app)

    database.register_teardown(app)

    assets = Environment(app)

    if configuration.app.debug:
        assets.url_expire = False
        js_thread = Bundle('js/thread.js', output='js/thread.debug.js')
        js_extra = Bundle('js/extra.js', output='js/extra.debug.js')
        css = Bundle('style/style.css', output='style/style.debug.css')
        css_extra = Bundle('style/extra.css', output='style/extra.debug.css')
        css_mod = Bundle('mod/style/mod_style.css', output='mod/style/mod_style.debug.css')
    else:
        assets.auto_build = False
        assets.manifest = 'json'
        js_thread = Bundle('js/thread.js', filters='jsmin', output='js/thread.min.js')
        js_extra = Bundle('js/extra.js', filters='jsmin', output='js/extra.min.js')
        css = Bundle('style/style.css', filters='cleancss', output='style/style.min.css')
        css_extra = Bundle('style/extra.css', filters='cleancss', output='style/extra.min.css')
        css_mod = Bundle('mod/style/mod_style.css', filters='cleancss', output='mod/style/mod_style.min.css')

    assets.register('js_thread', js_thread)
    assets.register('js_extra', js_extra)
    assets.register('css', css)
    assets.register('css_mod', css_mod)
    assets.register('css_extra', css_extra)

    from uchan.lib.cache import cache

    # Setup session handling
    from uchan.flask.custom_session import CustomSessionInterface
    app.session_interface = CustomSessionInterface(cache)

    # Import views
    import uchan.view

    # Import jinja filters
    import uchan.filter.app_filters

    # Import blueprints
    from uchan.view.mod import mod
    app.register_blueprint(mod)

    from uchan.view.api import api
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


def setup_logging():
    global app, logger, mod_logger

    import logging
    from logging.handlers import RotatingFileHandler

    app_log_path = configuration.app.app_log_path
    os.makedirs(os.path.dirname(app_log_path), exist_ok=True)

    log_format = '[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s'
    max_bytes = 5000000
    backup_count = 5

    app.logger.handlers[0].setFormatter(logging.Formatter(log_format))
    log_handler = RotatingFileHandler(app_log_path, maxBytes=max_bytes, backupCount=backup_count)
    log_handler.setFormatter(logging.Formatter(log_format))

    app.logger.addHandler(log_handler)

    if configuration.app.debug:
        log_handler.setLevel(logging.DEBUG)
        app.logger.setLevel(logging.DEBUG)
    else:
        log_handler.setLevel(logging.INFO)
        app.logger.setLevel(logging.INFO)

    logger = app.logger

    mod_log_path = configuration.app.mod_log_path
    os.makedirs(os.path.dirname(mod_log_path), exist_ok=True)
    mod_log_handler = RotatingFileHandler(mod_log_path, maxBytes=max_bytes, backupCount=backup_count)
    mod_log_handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))

    mod_logger = logging.getLogger('mod log')
    mod_logger.addHandler(mod_log_handler)
    mod_logger.setLevel(logging.INFO)


init()
