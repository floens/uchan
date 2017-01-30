from functools import wraps

from flask import Blueprint, jsonify

api = Blueprint('api', __name__, url_prefix='/api')


def jsonres():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            res = f(*args, **kwargs)
            return jsonify(res)

        return decorated_function

    return decorator


import uchan.view.api.views
