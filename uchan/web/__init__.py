from flask import Flask, request
from werkzeug.contrib.fixers import ProxyFix

from uchan import UchanConfiguration


class CustomFlaskApp(Flask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def reset_sessions(self, db, session_ids_to_skip):
        from uchan.lib.models import Session

        all_sessions = db.query(Session).all()
        for session_item in all_sessions:
            if session_item.session_id not in session_ids_to_skip:
                self.session_interface.delete_session(session_item.session_id)


def create_web_app(configuration: UchanConfiguration, app):
    if configuration.http.use_proxy_fixer:
        app.wsgi_app = ProxyFix(app.wsgi_app, configuration.http.proxy_fixer_num_proxies)

    app.config['DEBUG'] = configuration.app.debug
    app.config['APP_NAME'] = configuration.app.name
    app.config['MAX_CONTENT_LENGTH'] = configuration.http.max_content_length

    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True

    from uchan import logger
    from uchan.lib import BadRequestError

    # Setup error handlers
    @app.errorhandler(500)
    def server_error_handler(error):
        logger.exception(error)
        return app.send_static_file('500.html'), 500

    @app.errorhandler(404)
    def server_error_handler(error):
        logger.exception(error)
        return app.send_static_file('404.html'), 404

    def bad_request_message(e):
        if isinstance(e, BadRequestError):
            while isinstance(e, Exception) and len(e.args) > 0:
                e = e.args[0]

        return e if type(e) is str else ''

    from uchan.view import render_error

    @app.errorhandler(BadRequestError)
    def bad_request_handler(error):
        user_message = bad_request_message(error)

        return render_error(user_message, 400)

    from uchan.lib.action_authorizer import NoPermissionError, VerificationError

    @app.errorhandler(NoPermissionError)
    def no_permission_handler(error):
        return render_error('No permission', 401)

    from uchan.lib.proxy_request import get_request_ip4

    from uchan.lib.service import verification_service

    @app.errorhandler(VerificationError)
    def not_verified_handler(error):
        verification_service.handle_not_verified(error, request, get_request_ip4())
        return render_error(str(error), with_retry=True)

    @app.after_request
    def after_request_handler(response):
        verification_service.after_request(response)
        return response

    return app
