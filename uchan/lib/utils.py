import time


def now():
    return int(time.time() * 1000)


def ip4_to_str(ip4):
    outputs = []
    for i in range(4):
        n = (ip4 >> (3 - i) * 8) & 255
        outputs.append(str(n))

    return '.'.join(outputs)


def get_cookie_domain(app):
    """Helpful helper method that returns the cookie domain that should
    be used for the session cookie if session cookies are used.
    """
    if app.config['SESSION_COOKIE_DOMAIN'] is not None:
        return app.config['SESSION_COOKIE_DOMAIN']
    if app.config['SERVER_NAME'] is not None:
        # chop of the port which is usually not supported by browsers
        rv = '.' + app.config['SERVER_NAME'].rsplit(':', 1)[0]

        # Google chrome does not like cookies set to .localhost, so
        # we just go with no domain then.  Flask documents anyways that
        # cross domain cookies need a fully qualified domain name
        if rv == '.localhost':
            rv = None

        # If we infer the cookie domain from the server name we need
        # to check if we are in a subpath.  In that case we can't
        # set a cross domain cookie.
        if rv is not None:
            # Returns the path for which the cookie should be valid.  The
            # default implementation uses the value from the SESSION_COOKIE_PATH``
            # config var if it's set, and falls back to ``APPLICATION_ROOT`` or
            # uses ``/`` if it's `None`.

            path = app.config['SESSION_COOKIE_PATH'] or app.config['APPLICATION_ROOT'] or '/'
            if path != '/':
                rv = rv.lstrip('.')

        return rv
