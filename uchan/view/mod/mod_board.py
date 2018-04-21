from flask import request, redirect, url_for, render_template, abort, flash
from wtforms import StringField, SubmitField, IntegerField, BooleanField, HiddenField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, Length

from uchan import configuration
from uchan.lib import roles, validation
from uchan.lib.action_authorizer import NoPermissionError
from uchan.lib.exceptions import ArgumentError
from uchan.lib.mod_log import mod_log
from uchan.lib.model import ModeratorLogType, BoardModel
from uchan.lib.moderator_request import request_moderator
from uchan.lib.service import board_service, moderator_service
from uchan.view import check_csrf_token, with_token
from uchan.view.form import CSRFForm
from uchan.view.form.validators import BoardNameValidator, ModeratorUsernameValidator
from uchan.view.mod import mod


class AddBoardForm(CSRFForm):
    name = 'Create new board'
    action = '.mod_boards'

    board_name = StringField('Name', [DataRequired(), BoardNameValidator()],
                             description='Name of the board. This name is used in the url and cannot be changed, '
                                         'so choose carefully. You can have a maximum of (' +
                                         str(configuration.app.max_boards_per_moderator) + ') boards.')
    submit = SubmitField('Create board')


class BoardConfigurationForm(CSRFForm):
    name = 'Board configuration'

    for_action = HiddenField(default='configuration')

    full_name = StringField('Full name', [Length(max=25)], default='',
                            description='Full name of the board, this is displayed at the top.')
    description = TextAreaField('Description', [Length(max=100)],
                                description='Description of the board, this is displayed below the full name.',
                                render_kw={'cols': 60, 'rows': 6, 'placeholder': 'No description given'})

    pages = IntegerField('Pages', [DataRequired(), NumberRange(min=1, max=15)], default=10,
                         description='Number of pages for this board.')
    per_page = IntegerField('Per page', [DataRequired(), NumberRange(min=10, max=15)], default=15,
                            description='Number of threads per page.')
    bump_limit = IntegerField('Bump limit', [DataRequired(), NumberRange(min=100, max=500)], default=300,
                              description='Max count of posts in a thread that will bump.')
    file_posting = BooleanField('File posting', default=True,
                                description='Toggles file posting. This does not change posts currently '
                                            'up. May be overridden by a site-wide configuration.')
    posting_verification = BooleanField('Posting requires verification', default=False,
                                        description='Require a captcha for posting.')
    max_files = IntegerField('Max files', [DataRequired(), NumberRange(min=1, max=validation.MAX_FILES)], default=3,
                             description='Max number of files you can post per post.')

    submit = SubmitField('Update')


class InviteModeratorForm(CSRFForm):
    name = 'Invite moderator'
    action = '.mod_board'

    for_action = HiddenField(default='moderator_invite')

    username = StringField('Username', [DataRequired(), ModeratorUsernameValidator()],
                           description='Username of the moderator to invite to moderate this board.')

    submit = SubmitField('Invite')


@mod.route('/mod_board', methods=['GET', 'POST'])
def mod_boards():
    moderator = request_moderator()
    board_moderators = moderator_service.get_all_board_moderators_by_moderator(moderator)

    show_add_board = moderator_service.can_create_board(moderator)

    add_board_form = None
    if show_add_board:
        add_board_form = AddBoardForm(request.form)
        if request.method == 'POST' and add_board_form.validate():
            try:
                board_name = add_board_form.board_name.data
                moderator_service.user_create_board(moderator, board_name)
                flash('Board created')
                return redirect(url_for('.mod_board', board_name=board_name))
            except ArgumentError as e:
                flash(e.message)
                return redirect(url_for('.mod_boards'))

    return render_template('mod_boards.html', add_board_form=add_board_form, moderator=moderator,
                           board_moderators=board_moderators, show_add_board=show_add_board)


@mod.route('/mod_board/<board_name>', methods=['GET', 'POST'])
def mod_board(board_name):
    board = board_service.find_board(board_name)
    if not board:
        abort(404)

    moderator = request_moderator()
    if not moderator_service.moderates_board(moderator, board):
        abort(404)

    # These are purely for configuring the visibility of the various elements on the page,
    # the actions are still checked with the authorizer on post.
    can_update_board_config = moderator_service.can_update_board_config(moderator, board)
    can_update_advanced_board_configs = moderator_service.can_update_advanced_board_configs(moderator)
    can_update_roles = moderator_service.can_update_roles(moderator, board)
    can_invite_moderator = moderator_service.can_invite_moderator(moderator, board)
    can_remove_moderator = moderator_service.can_remove_moderator(moderator, board)
    can_delete = moderator_service.can_delete_board(moderator)

    for_action = request.form.get('for_action')
    action_configure = for_action == 'configuration'
    action_update_roles = for_action == 'update_roles'
    action_invite_moderator = for_action == 'moderator_invite'
    action_remove_moderator = for_action == 'moderator_remove'

    board_configuration_form = None
    invite_messages = []
    invite_moderator_form = None
    roles_messages = []

    if request.method == 'POST':
        if action_configure:
            board_configuration_form = BoardConfigurationForm(request.form)
            if board_configuration_form.validate():
                board.config.full_name = board_configuration_form.full_name.data
                board.config.description = board_configuration_form.description.data

                if can_update_advanced_board_configs:
                    board.config.pages = board_configuration_form.pages.data
                    board.config.per_page = board_configuration_form.per_page.data
                    board.config.bump_limit = board_configuration_form.bump_limit.data
                    board.config.file_posting = board_configuration_form.file_posting.data
                    board.config.posting_verification_required = board_configuration_form.posting_verification.data
                    board.config.max_files = board_configuration_form.max_files.data

                moderator_service.user_update_board_config(moderator, board)
        elif action_invite_moderator:
            invite_moderator_form = InviteModeratorForm(request.form)
            if invite_moderator_form.validate():
                moderator_username = invite_moderator_form.username.data

                try:
                    moderator_service.user_invite_moderator(request_moderator(), board, moderator_username)
                    invite_messages.append('Moderator invited')
                except ArgumentError as e:
                    invite_messages.append(str(e))
        elif action_remove_moderator:
            # No wtform for this action
            if not check_csrf_token(request.form.get('token')):
                abort(400)

            moderator_username = request.form['username']

            removed_self = False
            try:
                removed_self = moderator_service.user_remove_moderator(moderator, board, moderator_username)
                roles_messages.append('Moderator removed')
            except ArgumentError as e:
                roles_messages.append(str(e))

            if removed_self:
                return redirect(url_for('.mod_boards'))
        elif action_update_roles:
            # Also no wtform
            if not check_csrf_token(request.form.get('token')):
                abort(400)

            moderator_username = request.form['username']

            checked_roles = []
            for board_role in roles.ALL_BOARD_ROLES:
                if request.form.get(board_role) == 'on':
                    checked_roles.append(board_role)

            try:
                moderator_service.user_update_roles(moderator, board, moderator_username, checked_roles)
                roles_messages.append('Roles updated')
            except ArgumentError as e:
                roles_messages.append(str(e))
            except NoPermissionError as e:
                roles_messages.append('No permission')
        else:
            abort(400)

    if not board_configuration_form:
        board_configuration_form = BoardConfigurationForm(
            full_name=board.config.full_name,
            description=board.config.description,

            pages=board.config.pages,
            per_page=board.config.per_page,
            bump_limit=board.config.bump_limit,
            file_posting=board.config.file_posting,
            posting_verification=board.config.posting_verification_required,
            max_files=board.config.max_files
        )

    if not can_update_advanced_board_configs:
        del board_configuration_form.pages
        del board_configuration_form.per_page
        del board_configuration_form.bump_limit
        del board_configuration_form.file_posting
        del board_configuration_form.posting_verification
        del board_configuration_form.max_files

    if not invite_moderator_form:
        invite_moderator_form = InviteModeratorForm()

    board_configuration_form.action_url = url_for('.mod_board', board_name=board_name)
    invite_moderator_form.action_url = url_for('.mod_board', board_name=board_name, _anchor='invite')

    board_moderators = moderator_service.get_all_board_moderators_by_board(board)

    # Put the request moderator on top for the permissions table
    board_moderators_unsorted = sorted(board_moderators, key=lambda board_moderator: board_moderator.moderator.id)
    board_moderators = []
    for item in board_moderators_unsorted:
        if item.moderator == moderator:
            board_moderators.append(item)
            break
    for item in board_moderators_unsorted:
        if item.moderator != moderator:
            board_moderators.append(item)

    all_board_roles = roles.ALL_BOARD_ROLES

    return render_template('mod_board.html', board=board,
                           board_configuration_form=board_configuration_form,
                           invite_messages=invite_messages,
                           roles_messages=roles_messages,
                           invite_moderator_form=invite_moderator_form,
                           can_update_board_config=can_update_board_config,
                           can_update_advanced_board_configs=can_update_advanced_board_configs,
                           can_delete=can_delete,
                           can_update_roles=can_update_roles,
                           can_invite_moderator=can_invite_moderator,
                           can_remove_moderator=can_remove_moderator,
                           board_moderators=board_moderators,
                           all_board_roles=all_board_roles)


@mod.route('/mod_board/<board:board>/log')
@mod.route('/mod_board/<board:board>/log/<int(max=14):page>')
def mod_board_log(board: BoardModel, page=0):
    per_page = 100
    pages = 15

    moderator = request_moderator()

    logs = moderator_service.user_get_logs(moderator, board, page, per_page)

    def get_log_type(typeid):
        try:
            return ModeratorLogType(typeid).name
        except ValueError:
            return ''

    return render_template('mod_board_log.html', board=board, page=page, pages=pages,
                           logs=logs, get_log_type=get_log_type)


@mod.route('/mod_board/delete', methods=['POST'])
@with_token()
def mod_board_delete():
    board = board_service.find_board(request.form['board_name'])

    try:
        moderator_service.user_delete_board(request_moderator(), board)
        flash('Board deleted')
        mod_log('delete board /{}/'.format(board.name))
    except ArgumentError as e:
        flash(e.message)

    return redirect(url_for('.mod_boards'))
