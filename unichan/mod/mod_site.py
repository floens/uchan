from flask import request, render_template, abort, flash, redirect, url_for, session

from unichan import g, app
from unichan.database import get_db
from unichan.lib import roles, ArgumentError
from unichan.lib.configs import SiteConfig
from unichan.lib.models import Board, Post, Thread, Session, Ban, Report, Moderator, File, Config
from unichan.lib.proxy_request import get_request_ip4_str
from unichan.mod import mod, mod_role_restrict
from unichan.view import check_csrf_token, with_token


@mod.route('/mod_site', methods=['GET', 'POST'])
@mod_role_restrict(roles.ROLE_ADMIN)
def mod_site():
    site_config_row = g.config_service.get_config_by_type(SiteConfig.TYPE)
    site_config = g.config_service.load_config(site_config_row)

    if request.method == 'GET':
        session_count = get_db().query(Session).count()

        current_ip4_str = get_request_ip4_str()

        return render_template('mod_site.html', site_config_config=site_config, session_count=session_count, current_ip4_str=current_ip4_str)
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


@mod.route('/stat')
@mod_role_restrict(roles.ROLE_ADMIN)
def mod_stat():
    db = get_db()

    stats = {
        'board count': db.query(Board).count(),
        'thread count': db.query(Thread).count(),
        'post count': db.query(Post).count(),
        'ban count': db.query(Ban).count(),
        'report count': db.query(Report).count(),
        'session count': db.query(Session).count(),
        'moderator count': db.query(Moderator).count(),
        'file count': db.query(File).count(),
        'config count': db.query(Config).count()
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
