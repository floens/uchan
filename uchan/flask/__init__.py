from flask import Flask, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix

from uchan.config import UchanConfig


class CustomFlaskApp(Flask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def reset_sessions(self, session, session_ids_to_skip):
        from uchan.lib.ormmodel import SessionOrmModel

        all_sessions = session.query(SessionOrmModel).all()
        for session_item in all_sessions:
            if session_item.session_id not in session_ids_to_skip:
                self.session_interface.delete_session(session_item.session_id)


def create_web_app(config: UchanConfig, app):
    if config.use_proxy_fixer:
        app.wsgi_app = ProxyFix(app.wsgi_app, config.proxy_fixer_num_proxies)

    app.config["MAX_CONTENT_LENGTH"] = config.max_content_length

    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True

    import uchan.view.routing.converters

    uchan.view.routing.converters.init_converters(app)

    from uchan.lib.exceptions import BadRequestError

    # Setup error handlers
    @app.errorhandler(500)
    def server_error_handler(error):
        return send_from_directory("view/static", "500.html"), 404

    @app.errorhandler(404)
    def not_found_handler(error):
        return send_from_directory("view/static", "404.html"), 404

    def bad_request_message(e):
        if isinstance(e, BadRequestError):
            while isinstance(e, Exception) and len(e.args) > 0:
                e = e.args[0]

        return e if type(e) is str else ""

    from uchan.view import render_error

    @app.errorhandler(BadRequestError)
    def bad_request_handler(error):
        user_message = bad_request_message(error)

        return render_error(user_message, 400)

    from uchan.lib.action_authorizer import NoPermissionError

    @app.errorhandler(NoPermissionError)
    def no_permission_handler(error):
        return render_error("No permission", 401)

    from uchan.lib.service import verification_service

    @app.after_request
    def after_request_handler(response):
        verification_service.after_request(response)
        return response

    return app
