from flask import render_template, abort, request, flash, redirect, url_for

from unichan import g
from unichan.lib import roles, ArgumentError
from unichan.lib.models import Ban
from unichan.lib.utils import now
from unichan.mod import mod, mod_role_restrict
from unichan.view import with_token


def get_moderator_or_abort(moderator_id):
    moderator = g.moderator_service.find_moderator_id(moderator_id)
    if not moderator:
        abort(404)
    return moderator


@mod.route('/mod_ban')
@mod_role_restrict(roles.ROLE_ADMIN)
def mod_bans():
    bans = g.ban_service.get_all_bans()

    return render_template('mod_bans.html', bans=bans, ip4_to_str=g.ban_service.ip4_to_str)


@mod.route('/mod_ban/add', methods=['POST'])
@mod_role_restrict(roles.ROLE_ADMIN)
@with_token()
def mod_ban_add():
    ip4_raw = request.form['ban_ip4']
    ip4_end_raw = request.form.get('ban_ip4_end', None)
    ban_length = request.form.get('ban_length', type=int)
    if ban_length is None or ban_length < 0:
        abort(400)
    if ban_length > 24 * 31:
        flash('Ban too long')
        return redirect(url_for('.mod_bans'))

    reason = request.form['ban_reason']
    if len(reason) > 250:
        flash('Ban reason too long')
        return redirect(url_for('.mod_bans'))

    try:
        ip4 = g.ban_service.parse_ip4(ip4_raw)
        ip4_end = None
        if ip4_end_raw:
            ip4_end = g.ban_service.parse_ip4(ip4_end_raw)
    except ValueError:
        flash('Invalid ip')
        return redirect(url_for('.mod_bans'))

    ban = Ban()
    ban.ip4 = ip4
    if ip4_end is not None:
        ban.ip4_end = ip4_end
    ban.reason = reason
    ban.date = now()
    ban.length = ban_length * 60 * 60 * 1000

    try:
        g.ban_service.add_ban(ban)
        flash('Ban added')
    except ArgumentError as e:
        flash(e.message)

    return redirect(url_for('.mod_bans'))


@mod.route('/mod_ban/delete', methods=['POST'])
@mod_role_restrict(roles.ROLE_ADMIN)
@with_token()
def mod_ban_delete():
    ban_id = request.form.get('ban_id', type=int)
    if not ban_id:
        abort(400)

    ban = g.ban_service.find_ban_id(ban_id)
    if not ban:
        abort(404)

    g.ban_service.delete_ban(ban)
    flash('Ban deleted')

    return redirect(url_for('.mod_bans'))
