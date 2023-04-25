from flask import request, render_template, redirect, url_for
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import Length

from uchan.lib import roles
from uchan.lib.cache import cache
from uchan.lib.mod_log import mod_log
from uchan.lib.model import SiteConfigModel
from uchan.lib.proxy_request import get_request_ip4_str
from uchan.lib.service import site_service
from uchan.view import with_token
from uchan.view.form import CSRFForm
from uchan.view.mod import mod, mod_role_restrict


class SiteConfigurationForm(CSRFForm):
    name = 'Site configuration'
    action = '.mod_site'

    registration = BooleanField('Moderator registration', default=True,
                                description='Allow registration')
    board_creation = BooleanField('Board creation', default=True,
                                  description='Allow creation of boards by moderators. If disabled, only admins can '
                                              'create new boards.')
    motd = TextAreaField('MOTD', [Length(max=500)], default='',
                         description='The message of the day is displayed at the top of every board page.',
                         render_kw={'cols': 60, 'rows': 6})
    footer_text = TextAreaField('Footer text', [Length(max=100)], default='',
                                description='The footer text is displayed at the bottom of every page.',
                                render_kw={'cols': 60, 'rows': 6})
    boards_top = BooleanField('Boards at top', default=True,
                              description='Show board list at the top of every page.')
    default_name = StringField('Default posting name', [Length(max=25)], default='',
                               description='The default name for the posting form.')
    posting_enabled = BooleanField('Posting enabled', default=True,
                                   description='If unchecked, globally disables posting.')
    file_posting_enabled = BooleanField('File posting enabled', default=True,
                                        description='If unchecked, globally disables file posting.')
    header_tags = TextAreaField('Header tags', [Length(max=10000)], default='',
                                description='Additional html that is placed in the <head>.',
                                render_kw={'cols': 60, 'rows': 6})

    submit = SubmitField('Update')


@mod.route('/mod_site', methods=['GET', 'POST'])
@mod_role_restrict(roles.ROLE_ADMIN)
def mod_site():
    site_config: SiteConfigModel = site_service.get_site_config()

    site_configuration_form = None

    if request.method == 'POST':
        site_configuration_form = SiteConfigurationForm(request.form)
        if site_configuration_form.validate():
            site_config.registration = site_configuration_form.registration.data
            site_config.board_creation = site_configuration_form.board_creation.data
            site_config.motd = site_configuration_form.motd.data
            site_config.footer_text = site_configuration_form.footer_text.data
            site_config.boards_top = site_configuration_form.boards_top.data
            site_config.default_name = site_configuration_form.default_name.data
            site_config.posting_enabled = site_configuration_form.posting_enabled.data
            site_config.file_posting = site_configuration_form.file_posting_enabled.data
            site_config.header_tags = site_configuration_form.header_tags.data

            site_service.update_site_config(site_config)

    if not site_configuration_form:
        site_configuration_form = SiteConfigurationForm(
            registration=site_config.registration,
            board_creation=site_config.board_creation,
            motd=site_config.motd,
            footer_text=site_config.footer_text,
            boards_top=site_config.boards_top,
            default_name=site_config.default_name,
            posting_enabled=site_config.posting_enabled,
            file_posting_enabled=site_config.file_posting,
            header_tags=site_config.header_tags
        )

    current_ip4_str = get_request_ip4_str()
    memcache_stats = _gather_memcache_stats()
    db_stats = site_service.get_model_counts()

    return render_template('mod_site.html',
                           current_ip4_str=current_ip4_str,
                           memcache_stats=memcache_stats,
                           db_stats=db_stats,
                           site_configuration_form=site_configuration_form)


@mod.route('/mod_site/reset_sessions', methods=['POST'])
@mod_role_restrict(roles.ROLE_ADMIN)
@with_token()
def reset_sessions():
    mod_log('reset sessions')
    site_service.reset_sessions()
    return redirect(url_for('.mod_site'))


def _gather_memcache_stats():
    client = cache._client

    stats = client.get_stats()

    servers = []
    for stat in stats:
        s = 'server: ' + stat[0].decode('utf8') + '\n'
        t = []
        for k, v in stat[1].items():
            t.append((k, v))
        servers.append((s, t))
    return servers
