from flask import render_template, abort, request, flash, redirect, url_for
from markupsafe import Markup
from wtforms import StringField, IntegerField, SubmitField, TextAreaField
from wtforms.validators import NumberRange, DataRequired, IPAddress, Optional, Length

from uchan.filter.app_filters import formatted_time, time_remaining
from uchan.lib import roles
from uchan.lib.exceptions import ArgumentError
from uchan.lib.mod_log import mod_log
from uchan.lib.model import BanModel
from uchan.lib.ormmodel import BanOrmModel
from uchan.lib.proxy_request import parse_ip4
from uchan.lib.repository import bans
from uchan.lib.service import ban_service, posts_service
from uchan.lib.utils import ip4_to_str, now
from uchan.view import with_token
from uchan.view.form import CSRFForm
from uchan.view.form.validators import BoardNameValidator
from uchan.view.mod import mod, mod_role_restrict
from uchan.view.mod.paged_model import PagedModel


class BanForm(CSRFForm):
    name = 'Add ban'
    action = '.mod_bans'

    ban_ip4 = StringField('IPv4 address', [DataRequired(), IPAddress(ipv4=True, ipv6=False)],
                          description='IPv4 address to ban.',
                          render_kw={'placeholder': '123.123.123.123'})
    ban_ip4_end = StringField('IPv4 address end range', [Optional(), IPAddress(ipv4=True, ipv6=False)],
                              description='If specified then IPv4 range from start to end will be banned.',
                              render_kw={'placeholder': '123.123.123.123'})
    board = StringField('Board code', [Optional(), BoardNameValidator()],
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


class PagedBans(PagedModel):
    def provide_count(self):
        return bans.count()

    def provide_data(self, offset: int, limit: int):
        return bans.get_all(offset, limit)

    def limit(self):
        return 50

    def header(self):
        return 'ip', 'to ip', 'from', 'until', 'board', 'reason', ''

    def row(self, ban: BanOrmModel):
        if ban.length > 0:
            expire_time = ban.date + ban.length
            until = formatted_time(expire_time) + ' - '
            if expire_time - now() < 0:
                until += 'Expired, not viewed'
            else:
                until += time_remaining(expire_time) + ' remaining'
        else:
            until = 'Does not expire'

        delete_button = '<button class="confirm-button" name="ban_id" value="' + str(ban.id) + '">Lift ban</button>'

        return (
            ip4_to_str(ban.ip4),
            ip4_to_str(ban.ip4_end) if ban.ip4_end is not None else '',
            formatted_time(ban.date),
            until,
            ban.board or '',
            ban.reason,
            Markup(delete_button)
        )


# TODO: add search
@mod.route('/mod_ban', methods=['GET', 'POST'])
@mod_role_restrict(roles.ROLE_ADMIN)
def mod_bans():
    ban_messages = []

    if request.method == 'POST':
        ban_form = BanForm(request.form)
        if ban_form.validate():
            ip4 = parse_ip4(ban_form.ban_ip4.data)
            ip4_end_form = ban_form.ban_ip4_end.data
            ip4_end = parse_ip4(ip4_end_form) if ip4_end_form else None

            ban = BanModel()
            ban.ip4 = ip4
            if ip4_end is not None:
                ban.ip4_end = ip4_end
            ban.reason = ban_form.reason.data
            board_form = ban_form.board.data
            ban.board = board_form if board_form else None
            ban.length = ban_form.duration.data * 60 * 60 * 1000

            try:
                ban_service.add_ban(ban)
                ban_messages.append('Ban added')
            except ArgumentError as e:
                ban_messages.append(e.message)
    else:
        # Searches for the ip4 of the post and fills it in if for_post was set to a post id
        filled_in_ip4 = ''
        for_post_id = request.args.get('for_post', None)
        if for_post_id:
            post = posts_service.find_post(for_post_id)
            if post:
                filled_in_ip4 = ip4_to_str(post.ip4)
        ban_form = BanForm(None, ban_ip4=filled_in_ip4)

    return render_template('mod_bans.html', ban_messages=ban_messages, ban_form=ban_form, paged_bans=PagedBans())


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
