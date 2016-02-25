from flask.globals import _request_ctx_stack
from uchan import g
from uchan.lib.moderator_request import get_authed_moderator, get_authed
from uchan.lib.proxy_request import get_request_ip4_str


def mod_log(what, moderator_name=None, ip4_str=None):
    # Hax
    in_request_context = _request_ctx_stack.top is not None

    if in_request_context:
        if ip4_str is None:
            ip4_str = get_request_ip4_str()
        if moderator_name is None:
            moderator_name = get_authed_moderator().username if get_authed() else None

    output = ''
    if ip4_str is not None:
        output += '[' + ip4_str + '] '
    if moderator_name is not None:
        output += '[' + moderator_name + '] '
    output += what

    g.mod_logger.info(output)
