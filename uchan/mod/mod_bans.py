from flask import render_template, abort, request, flash, redirect, url_for
from wtforms import Form, StringField, IntegerField, SubmitField, TextAreaField
from wtforms.validators import NumberRange, DataRequired, IPAddress, ValidationError, Optional

from uchan.lib import roles, ArgumentError
from uchan.lib.mod_log import mod_log
from uchan.lib.models import Ban
from uchan.lib.proxy_request import parse_ip4
from uchan.lib.service import ban_service, board_service
from uchan.lib.utils import ip4_to_str
from uchan.mod import mod, mod_role_restrict
from uchan.view import with_token


def board_input(form, field):
    if not board_service.check_board_name_validity(field.data):
        raise ValidationError('Board name not valid.')


class BanForm(Form):
    name = 'Add ban'
    action = '.mod_bans'

    ban_ip4 = StringField('IPv4 address', [DataRequired(), IPAddress(ipv4=True, ipv6=False)],
                          description='IPv4 address to ban.',
                          render_kw={'placeholder': '123.123.123.123'})
    ban_ip4_end = StringField('IPv4 address end range', [Optional(), IPAddress(ipv4=True, ipv6=False)],
                              description='If specified then IPv4 range from start to end will be banned.',
                              render_kw={'placeholder': '123.123.123.123'})
    board = StringField('Board code', [Optional(), board_input],
                        description='If specified then the ban will be restricted to the given board, '
                                    'otherwise the ban is for all boards.',
                        render_kw={'placeholder': 'a'})
    duration = IntegerField('Ban duration', [DataRequired(), NumberRange(min=0, max=None)], default=24,
                            description='Ban duration in hours. Use 0 for a permanent ban.',
                            render_kw={'placeholder': '24'})
    reason = TextAreaField('Ban reason', description='This will be shown to the user on the banned page.',
                           render_kw={'cols': 60, 'rows': 6, 'placeholder': 'Banned!'}),
    submit = SubmitField('Ban')


@mod.route('/mod_ban', methods=['GET', 'POST'])
@mod_role_restrict(roles.ROLE_ADMIN)
def mod_bans():
    ban_form = BanForm(request.form)
    if request.method == 'POST':
        ban_form.validate()

    bans = ban_service.get_all_bans()

    return render_template('mod_bans.html', ban_form=ban_form, bans=bans)


# @mod.route('/mod_ban')
# @mod_role_restrict(roles.ROLE_ADMIN)
# def mod_bans():
#     bans = ban_service.get_all_bans()
#
#     ban_ip4 = ''
#     post_id = request.args.get('for_post', None)
#     if post_id:
#         post = posts_service.find_post(post_id)
#         if post:
#             ban_ip4 = ip4_to_str(post.ip4)
#
#     n = now()
#     return render_template('mod_bans.html', ban_ip4=ban_ip4, bans=bans, ip4_to_str=ip4_to_str, now=n)


@mod.route('/mod_ban/add', methods=['POST'])
@mod_role_restrict(roles.ROLE_ADMIN)
# @with_token()
def mod_ban_add():
    ban_form = BanForm(request.form)
    if ban_form.validate():
        flash('Form validated!')

    """ip4_raw = request.form['ban_ip4']
    if not ip4_raw or len(ip4_raw) > 25:
        abort(400)

    ip4_end_raw = request.form.get('ban_ip4_end', None)
    if not ip4_end_raw:
        ip4_end_raw = None
    if ip4_end_raw is not None and (len(ip4_end_raw) == 0 or len(ip4_end_raw) > 25):
        abort(400)

    board = request.form.get('board', None)
    if not board:
        board = None
    if board is not None and not board_service.check_board_name_validity(board):
        abort(400)

    ban_length_hours = request.form.get('ban_length', type=int)
    if ban_length_hours is None or ban_length_hours < 0:
        abort(400)

    reason = request.form['ban_reason']

    try:
        ip4 = parse_ip4(ip4_raw)
        ip4_end = None
        if ip4_end_raw:
            ip4_end = parse_ip4(ip4_end_raw)
    except ValueError:
        flash('Invalid ip')
        return redirect(url_for('.mod_bans'))

    ban = Ban()
    ban.ip4 = ip4
    if ip4_end is not None:
        ban.ip4_end = ip4_end
    ban.reason = reason
    ban.board = board
    ban.length = ban_length_hours * 60 * 60 * 1000

    try:
        ban_service.add_ban(ban)
        flash('Ban added')
        mod_log('ban add {} from {} to {}{} for {} hours reason {}'.format(
            ban.id, ip4_to_str(ip4), ip4_to_str(ip4_end) if ip4_end is not None else '-',
            ' on {}'.format(board) if board else '', ban_length_hours, reason))
    except ArgumentError as e:
        flash(e.message)"""

    return redirect(url_for('.mod_bans'))


@mod.route('/mod_ban/delete', methods=['POST'])
@mod_role_restrict(roles.ROLE_ADMIN)
@with_token()
def mod_ban_delete():
    ban_id = request.form.get('ban_id', type=int)
    if not ban_id or ban_id < 0:
        abort(400)

    ban = ban_service.find_ban_id(ban_id)
    if not ban:
        abort(404)

    ban_service.delete_ban(ban)
    flash('Ban deleted')
    mod_log('ban delete {}'.format(ban_id))

    return redirect(url_for('.mod_bans'))
