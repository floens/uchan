from wtforms import ValidationError

from uchan.lib.service import board_service


class BoardValidator:
    def __call__(self, form, field):
        if not board_service.check_board_name_validity(field.data):
            raise ValidationError('Board name not valid.')
