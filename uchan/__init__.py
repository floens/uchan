import os

from celery import Celery
from celery.loaders.app import AppLoader

app = None
celery = None
logger = None
mod_logger = None


class CustomCeleryLoader(AppLoader):
    def on_process_cleanup(self):
        from uchan.lib import database

        database.clean_up()


from uchan.config import UchanConfig  # noqa

config: UchanConfig


def init():
    global app, celery, config

    config = UchanConfig()

    import uchan.lib.database as database

    database.init_db()

    celery = Celery("uchan", loader=CustomCeleryLoader)
    celery.config_from_object(
        {
            "result_backend": "rpc://",
            "task_serializer": "pickle",
            "accept_content": ["pickle"],
            "result_serializer": "pickle",
            "broker_url": config.broker_url,
        }
    )

    # Import it here so that the templates resolve correctly
    from uchan.flask import CustomFlaskApp, create_web_app

    app = CustomFlaskApp(__name__, template_folder="view/templates", static_folder=None)
    setup_logging()
    create_web_app(config, app)

    database.register_teardown(app)

    # Setup session handling
    from uchan.flask.custom_session import CustomSessionInterface
    from uchan.lib.cache import cache

    app.session_interface = CustomSessionInterface(cache)

    # Import views
    import uchan.view
    from uchan.view import assets

    assets.setup_assets(app, config.asset_watch_for_changes)

    # Import jinja filters
    import uchan.filter.app_filters

    # Import blueprints
    from uchan.view.mod import mod

    app.register_blueprint(mod)

    from uchan.view.api import api

    app.register_blueprint(api)

    from uchan.lib.service.file_service import LocalCdn

    if config.file_cdn_type == "local":
        cdn = LocalCdn(config.local_cdn_path, config.local_cdn_web_path)
    else:
        raise Exception("Unknown file cdn type")

    from uchan.lib.service import file_service

    file_service.init(config.upload_queue_path, cdn)

    # Register tasks
    import uchan.lib.tasks  # noqa

    # print('Loading plugins')

    from uchan.lib import plugin_manager

    # plugins = list(
    #     map(str.strip, config_parser['plugins']['plugins'].split(',')))
    # plugin_manager.load_plugins(plugins, config_parser)

    # FIXME: remove or improve "plugin" system
    plugin_manager.load_plugins(["captcha2"])

    # database.metadata_create_all()


def setup_logging():
    global app, logger, mod_logger

    import logging
    from logging.handlers import RotatingFileHandler

    app_log_path = config.app_log_path
    os.makedirs(os.path.dirname(app_log_path), exist_ok=True)

    log_format = "[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s"
    max_bytes = 5000000
    backup_count = 5

    # app.logger.handlers[0].setFormatter(logging.Formatter(log_format))
    log_handler = RotatingFileHandler(
        app_log_path, maxBytes=max_bytes, backupCount=backup_count
    )
    log_handler.setFormatter(logging.Formatter(log_format))

    app.logger.addHandler(log_handler)

    if config.debug:
        log_handler.setLevel(logging.DEBUG)
        app.logger.setLevel(logging.DEBUG)
    else:
        log_handler.setLevel(logging.INFO)
        app.logger.setLevel(logging.INFO)

    logger = app.logger

    mod_log_path = config.mod_log_path
    os.makedirs(os.path.dirname(mod_log_path), exist_ok=True)
    mod_log_handler = RotatingFileHandler(
        mod_log_path, maxBytes=max_bytes, backupCount=backup_count
    )
    mod_log_handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))

    mod_logger = logging.getLogger("mod log")
    mod_logger.addHandler(mod_log_handler)
    mod_logger.setLevel(logging.INFO)


init()
