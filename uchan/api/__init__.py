from flask import Blueprint

api = Blueprint('api', __name__, url_prefix='/api')

import uchan.api.views
