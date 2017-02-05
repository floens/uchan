from flask import render_template, request, flash, url_for
from wtforms import PasswordField, SubmitField
from wtforms import ValidationError
from wtforms.validators import Length

from uchan.lib.exceptions import ArgumentError
from uchan.lib.mod_log import mod_log
from uchan.lib.moderator_request import request_moderator
from uchan.lib.service import moderator_service
from uchan.view.form import CSRFForm
from uchan.view.mod import mod


def password_input(form, field):
    if not moderator_service.check_password_validity(field.data):
        raise ValidationError('Password not valid.')


class ChangePasswordForm(CSRFForm):
    name = 'Change password'
    action = '.mod_self'

    old_password = PasswordField('Old password', [Length(min=moderator_service.PASSWORD_MIN_LENGTH), password_input])
    new_password = PasswordField('New password', [Length(min=moderator_service.PASSWORD_MIN_LENGTH), password_input])
    submit = SubmitField('Update password')


@mod.route('/mod_self', methods=['GET', 'POST'])
def mod_self():
    moderator = request_moderator()

    change_password_form = ChangePasswordForm(request.form)
    if request.method == 'POST' and change_password_form.validate():
        try:
            moderator_service.change_password(
                moderator, change_password_form.old_password.data, change_password_form.new_password.data)
            flash('Changed password')
            mod_log('password changed')
        except ArgumentError as e:
            flash(e.message)

    board_links = map(lambda b: (b.name, url_for('board', board_name=b.name)), moderator.boards)

    return render_template('mod_self.html', change_password_form=change_password_form, moderator=moderator,
                           board_links=board_links)
