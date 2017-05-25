from wtforms import ValidationError

from uchan.lib import validation
from uchan.lib.service import board_service, moderator_service


class BoardValidator:
    def __call__(self, form, field):
        if not validation.check_board_name_validity(field.data):
            raise ValidationError('Board name not valid.')

        board = board_service.find_board(field.data)
        if not board:
            raise ValidationError('Board does not exist')
        field.board = board


class BoardNameValidator:
    def __call__(self, form, field):
        if not validation.check_board_name_validity(field.data):
            raise ValidationError('Board name not valid.')


class ModeratorUsernameValidator:
    def __call__(self, form, field):
        if not validation.check_username_validity(field.data):
            raise ValidationError('Username not valid')


class ModeratorPasswordValidator:
    def __call__(self, form, field):
        if not validation.check_password_validity(field.data):
            raise ValidationError('Password not valid')
