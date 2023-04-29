from flask.globals import _request_ctx_stack


def mod_log(what, moderator_name=None, moderator=None, ip4_str=None):
    """Logs to a log file."""
    # Hax
    in_request_context = _request_ctx_stack.top is not None

    if in_request_context:
        if ip4_str is None:
            ip4_str = get_request_ip4_str()
        if moderator_name is None:
            if not moderator:
                moderator = request_moderator() if get_authed() else None
            if moderator is not None:
                moderator_name = moderator.username

    output = ""
    if ip4_str is not None:
        output += "[" + ip4_str + "] "
    if moderator_name is not None:
        output += "[" + moderator_name + "] "
    output += what

    mod_logger.info(output)


from uchan import mod_logger  # noqa
from uchan.lib.moderator_request import request_moderator, get_authed  # noqa
from uchan.lib.proxy_request import get_request_ip4_str  # noqa
