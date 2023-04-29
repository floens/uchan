from wtforms import Form
from wtforms.csrf.core import CSRF

from uchan.view import check_csrf_token, generate_csrf_token


class CSRFImpl(CSRF):
    def generate_csrf_token(self, csrf_token_field):
        return generate_csrf_token()

    def validate_csrf_token(self, form, field):
        if not check_csrf_token(field.data):
            raise ValueError("Invalid CSRF token")


class CSRFForm(Form):
    class Meta:
        csrf = True
        csrf_class = CSRFImpl
        csrf_field_name = "token"
