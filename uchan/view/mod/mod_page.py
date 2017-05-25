from flask import request, redirect, url_for, render_template, abort, flash

from uchan.lib import roles
from uchan.lib.exceptions import ArgumentError
from uchan.lib.mod_log import mod_log
from uchan.lib.model import PageModel
from uchan.lib.ormmodel import PageOrmModel
from uchan.lib.service import page_service
from uchan.view import with_token
from uchan.view.mod import mod, mod_role_restrict


@mod.route('/mod_page')
@mod_role_restrict(roles.ROLE_ADMIN)
def mod_pages():
    pages = page_service.get_all_pages()
    page_types = page_service.get_page_types()

    return render_template('mod_pages.html', pages=pages, page_types=page_types)


@mod.route('/mod_page/add', methods=['POST'])
@mod_role_restrict(roles.ROLE_ADMIN)
@with_token()
def mod_page_add():
    page_title = request.form['page_title']
    page_link_name = request.form['page_link_name']
    page_type = request.form['page_type']

    page = PageModel.from_title_link_type(page_title, page_link_name, page_type)

    try:
        page_service.create_page(page)
        flash('Page added')
        mod_log('page {} added'.format(page_link_name))
    except ArgumentError as e:
        flash(e.message)

    return redirect(url_for('.mod_pages'))


@mod.route('/mod_page/delete', methods=['POST'])
@mod_role_restrict(roles.ROLE_ADMIN)
@with_token()
def mod_page_delete():
    page = page_service.find_page_id(request.form.get('page_id', type=int))

    page_service.delete_page(page)
    flash('Page deleted')
    mod_log('page {} deleted'.format(page.link_name))

    return redirect(url_for('.mod_pages'))


@mod.route('/mod_page/<page:page>')
@mod_role_restrict(roles.ROLE_ADMIN)
def mod_page(page: PageModel):
    return render_template('mod_page.html', page=page)


@mod.route('/mod_page/<page:page>/update', methods=['POST'])
@mod_role_restrict(roles.ROLE_ADMIN)
@with_token()
def mod_page_update(page: PageModel):
    page.title = request.form['page_title']
    page.content = request.form['page_content']
    page.order = request.form.get('page_order', type=int)
    if page.order is None:
        page.order = 0

    try:
        page_service.update_page(page)
        flash('Page updated')
        mod_log('page {} updated'.format(page.link_name))
    except ArgumentError as e:
        flash(e.message)

    return redirect(url_for('.mod_page', page=page))
