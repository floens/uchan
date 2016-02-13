from flask import request, redirect, url_for, render_template, abort, session, flash

from unichan import app, g
from unichan.database import get_db
from unichan.lib import roles, ArgumentError
from unichan.lib.configs import SiteConfig
from unichan.lib.models import Board, Post, Report, Session, Thread, Moderator
from unichan.lib.moderator_request import get_authed, unset_mod_authed, set_mod_authed, get_authed_moderator
from unichan.mod import mod, mod_role_restrict
from unichan.view import check_csrf_token, with_token


@mod.route('/')
def mod_index():
    return redirect(url_for('.mod_auth'))


@mod.route('/auth', methods=['GET', 'POST'])
def mod_auth():
    if request.method == 'POST':
        if not check_csrf_token(request.form.get('token')):
            abort(400)

        if get_authed():
            if request.form.get('deauth') == 'yes':
                unset_mod_authed()
        else:
            username = request.form['username']
            password = request.form['password']

            mod_service = g.moderator_service

            if not mod_service.check_username_validity(username) or not mod_service.check_password_validity(password):
                flash('Invalid username or password')
            else:
                moderator = mod_service.find_moderator_username(username)
                if not moderator:
                    flash('Invalid username or password')
                else:
                    try:
                        mod_service.check_password(moderator, password)
                        set_mod_authed(moderator)
                        flash('Logged in')
                    except ArgumentError:
                        flash('Invalid username or password')

        return redirect(url_for('.mod_auth'))
    else:
        authed = get_authed()
        moderator = get_authed_moderator() if authed else None
        return render_template('auth.html', authed=authed, moderator=moderator)


@mod.route('/mod_post')
def mod_post():
    reports = get_db().query(Report).all()

    return render_template('mod_post.html', reports=reports)


@mod.route('/stat')
@mod_role_restrict(roles.ROLE_ADMIN)
def mod_stat():
    db = get_db()

    stats = {
        'board_count': db.query(Board).count(),
        'thread_count': db.query(Thread).count(),
        'post_count': db.query(Post).count()
    }

    return render_template('stat.html', stats=stats)


@mod.route('/memcache_stat')
@mod_role_restrict(roles.ROLE_ADMIN)
def mod_memcache_stat():
    client = g.memcached_cache._client

    stats = client.get_stats()

    servers = []
    for stat in stats:
        s = 'server: ' + stat[0].decode('utf8') + '\n'
        t = []
        for k, v in stat[1].items():
            t.append((k.decode('utf8'), v.decode('utf8')))
        servers.append((s, t))

    return render_template('memcache_stat.html', stats=servers)


@mod.route('/mod_moderator')
@mod_role_restrict(roles.ROLE_ADMIN)
def mod_moderators():
    moderators = g.moderator_service.get_all_moderators()

    return render_template('mod_moderators.html', moderators=moderators)


@mod.route('/mod_moderator/add', methods=['POST'])
@mod_role_restrict(roles.ROLE_ADMIN)
@with_token()
def mod_moderator_add():
    moderator_name = request.form['moderator_name']
    if not g.moderator_service.check_username_validity(moderator_name):
        flash('Invalid moderator name')
        return redirect(url_for('.mod_moderators'))

    moderator_password = request.form['moderator_password']
    if not g.moderator_service.check_password_validity(moderator_password):
        flash('Invalid moderator password')
        return redirect(url_for('.mod_moderators'))

    moderator = Moderator()
    moderator.roles = []
    moderator.username = moderator_name

    try:
        g.moderator_service.create_moderator(moderator, moderator_password)
    except ArgumentError as e:
        flash(e.message)
    flash('Moderator added')

    return redirect(url_for('.mod_moderators'))


@mod.route('/mod_moderator/delete', methods=['POST'])
@mod_role_restrict(roles.ROLE_ADMIN)
@with_token()
def mod_moderator_delete():
    moderator_id = request.form['moderator_id']

    moderator = g.moderator_service.find_moderator_id(moderator_id)
    if not moderator:
        abort(404)

    g.moderator_service.delete_moderator(moderator)
    flash('Moderator deleted')

    return redirect(url_for('.mod_moderators'))


@mod.route('/mod_moderator/<int:moderator_id>')
@mod_role_restrict(roles.ROLE_ADMIN)
def mod_moderator(moderator_id):
    moderator = g.moderator_service.find_moderator_id(moderator_id)
    if not moderator:
        abort(404)

    return render_template('mod_moderator.html', moderator=moderator)


@mod.route('/mod_moderator/<int:moderator_id>/board_add', methods=['POST'])
@mod_role_restrict(roles.ROLE_ADMIN)
@with_token()
def mod_moderator_board_add(moderator_id):
    moderator = g.moderator_service.find_moderator_id(moderator_id)
    if not moderator:
        abort(404)

    board_name = request.form['board_name']
    board = g.board_service.find_board(board_name)
    if board is None:
        flash('That board does not exist')
    else:
        g.board_service.board_add_moderator(board, moderator)
        flash('Board added to moderator')

    return redirect(url_for('.mod_moderator', moderator_id=moderator_id))


@mod.route('/mod_moderator/<int:moderator_id>/board_remove', methods=['POST'])
@mod_role_restrict(roles.ROLE_ADMIN)
@with_token()
def mod_moderator_board_remove(moderator_id):
    moderator = g.moderator_service.find_moderator_id(moderator_id)
    if not moderator:
        abort(404)

    board_name = request.form['board_name']
    board = g.board_service.find_board(board_name)
    if board is None:
        flash('That board does not exist')
    else:
        g.board_service.board_remove_moderator(board, moderator)
        flash('Board removed from moderator')

    return redirect(url_for('.mod_moderator', moderator_id=moderator_id))


@mod.route('/mod_moderator/<int:moderator_id>/change_password', methods=['POST'])
@mod_role_restrict(roles.ROLE_ADMIN)
@with_token()
def mod_moderator_password(moderator_id):
    moderator = g.moderator_service.find_moderator_id(moderator_id)
    if not moderator:
        abort(404)

    old_password = request.form['old_password']
    new_password = request.form['new_password']

    try:
        g.moderator_service.change_password(moderator, old_password, new_password)
        flash('Changed password')
    except ArgumentError as e:
        flash(e.message)

    return redirect(url_for('.mod_moderator', moderator_id=moderator_id))


@mod.route('/mod_board')
@mod_role_restrict(roles.ROLE_ADMIN)
def mod_boards():
    boards = g.board_service.get_all_boards()

    return render_template('mod_boards.html', boards=boards)


@mod.route('/mod_board/add', methods=['POST'])
@mod_role_restrict(roles.ROLE_ADMIN)
@with_token()
def mod_board_add():
    board_name = request.form['board_name']

    if not g.board_service.check_board_name_validity(board_name):
        flash('Invalid board name')
        return redirect(url_for('.mod_boards'))

    board = Board()
    board.name = board_name

    try:
        g.board_service.add_board(board)
        flash('Board added')
    except ArgumentError as e:
        flash(e.message)

    return redirect(url_for('.mod_board', board_name=board.name))


@mod.route('/mod_board/delete', methods=['POST'])
@mod_role_restrict(roles.ROLE_ADMIN)
@with_token()
def mod_board_delete():
    board_name = request.form['board_name']

    board = g.board_service.find_board(board_name)
    if not board:
        abort(404)

    g.board_service.delete_board(board)
    flash('Board deleted')

    return redirect(url_for('.mod_boards'))


@mod.route('/mod_board/<board_name>', methods=['GET', 'POST'])
@mod_role_restrict(roles.ROLE_ADMIN)
def mod_board(board_name):
    board = g.board_service.find_board(board_name)
    if not board:
        abort(404)

    board_config_row = board.config
    board_config = g.config_service.load_config(board_config_row)

    if request.method == 'GET':
        return render_template('mod_board.html', board=board, board_config=board_config)
    else:
        form = request.form

        if not check_csrf_token(form.get('token')):
            abort(400)

        try:
            g.config_service.save_from_form(board_config, board_config_row, form)
            flash('Board config updated')
            g.board_cache.invalidate_board_config(board_name)
        except ArgumentError as e:
            flash(str(e))

        return redirect(url_for('.mod_board', board_name=board_name))


@mod.route('/mod_site', methods=['GET', 'POST'])
@mod_role_restrict(roles.ROLE_ADMIN)
def mod_site():
    site_config_row = g.config_service.get_config_by_type(SiteConfig.TYPE)
    site_config = g.config_service.load_config(site_config_row)

    if request.method == 'GET':
        session_count = get_db().query(Session).count()

        return render_template('mod_site.html', site_config=site_config, session_count=session_count)
    else:
        form = request.form

        if not check_csrf_token(form.get('token')):
            abort(400)

        try:
            g.config_service.save_from_form(site_config, site_config_row, form, 'mod_site_')
            flash('Site config updated')
            g.site_cache.invalidate_site_config()
        except ArgumentError as e:
            flash(str(e))

        return redirect(url_for('.mod_site'))


@mod.route('/mod_site/reset_sessions', methods=['POST'])
@mod_role_restrict(roles.ROLE_ADMIN)
@with_token()
def reset_sessions():
    app.reset_sessions(get_db(), [session.session_id])
    return redirect(url_for('.mod_site'))
