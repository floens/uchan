from flask import render_template, abort, request, flash, redirect, url_for
from wtforms import Form, StringField, IntegerField, SubmitField, TextAreaField
from wtforms.validators import NumberRange, DataRequired, IPAddress, ValidationError, Optional, Length

from uchan.lib import roles, ArgumentError
from uchan.lib.mod_log import mod_log
from uchan.lib.models import Ban
from uchan.lib.proxy_request import parse_ip4
from uchan.lib.service import ban_service, board_service, posts_service
from uchan.lib.utils import ip4_to_str
from uchan.mod import mod, mod_role_restrict
from uchan.view import with_token, check_csrf_token
from uchan.view.form import CSRFForm


def board_input(form, field):
    if not board_service.check_board_name_validity(field.data):
        raise ValidationError('Board name not valid.')


class BanForm(CSRFForm):
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
    reason = TextAreaField('Ban reason', [Length(max=ban_service.MAX_REASON_LENGTH)],
                           description='This will be shown to the user on the banned page.',
                           render_kw={'cols': 60, 'rows': 6, 'placeholder': 'Banned!'})
    submit = SubmitField('Ban')


@mod.route('/mod_ban', methods=['GET', 'POST'])
@mod_role_restrict(roles.ROLE_ADMIN)
def mod_bans():
    if request.method == 'POST':
        ban_form = BanForm(request.form)
        if ban_form.validate():
            ip4 = parse_ip4(ban_form.ban_ip4.data)
            ip4_end_form = ban_form.ban_ip4_end.data
            ip4_end = parse_ip4(ip4_end_form) if ip4_end_form else None

            ban = Ban()
            ban.ip4 = ip4
            if ip4_end is not None:
                ban.ip4_end = ip4_end
            ban.reason = ban_form.reason.data
            board_form = ban_form.board.data
            ban.board = board_form if board_form else None
            ban.length = ban_form.duration.data * 60 * 60 * 1000

            try:
                ban_service.add_ban(ban)
                flash('Ban added')
                mod_log('ban add {} from {} to {}{} for {} hours reason {}'.format(
                    ban.id, ip4_to_str(ip4), ip4_to_str(ip4_end) if ip4_end is not None else '-',
                    ' on {}'.format(ban.board) if ban.board else '', ban_form.duration.data, ban_form.reason.data))
            except ArgumentError as e:
                flash(e.message)
    else:
        # Searches for the ip4 of the post and fills it in if for_post was set to a post id
        filled_in_ip4 = ''
        for_post_id = request.args.get('for_post', None)
        if for_post_id:
            post = posts_service.find_post(for_post_id)
            if post:
                filled_in_ip4 = ip4_to_str(post.ip4)
        ban_form = BanForm(None, ban_ip4=filled_in_ip4)

    bans = ban_service.get_all_bans()

    return render_template('mod_bans.html', ban_form=ban_form, bans=bans)


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
    flash('Ban lifted')
    mod_log('ban delete {}'.format(ban_id))

    return redirect(url_for('.mod_bans'))
