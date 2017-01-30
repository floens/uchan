from flask import request, redirect, url_for, render_template, abort, flash

from uchan.lib import roles, ArgumentError
from uchan.lib.mod_log import mod_log
from uchan.lib.models import Page
from uchan.lib.service import page_service
from uchan.view import with_token
from uchan.view.mod import mod, mod_role_restrict


def get_page_or_abort(page_id):
    if not page_id:
        abort(400)

    page = page_service.find_page_id(page_id)
    if not page:
        abort(404)
    return page


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

    page = Page()
    page.title = page_title
    page.link_name = page_link_name
    page.type = page_type
    page.order = 0
    page.content = ''

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
    page = get_page_or_abort(request.form.get('page_id', type=int))

    page_service.delete_page(page)
    flash('Page deleted')
    mod_log('page {} deleted'.format(page.link_name))

    return redirect(url_for('.mod_pages'))


@mod.route('/mod_page/<int:page_id>')
@mod_role_restrict(roles.ROLE_ADMIN)
def mod_page(page_id):
    page = get_page_or_abort(page_id)

    return render_template('mod_page.html', page=page)


@mod.route('/mod_page/<int:page_id>/update', methods=['POST'])
@mod_role_restrict(roles.ROLE_ADMIN)
@with_token()
def mod_page_update(page_id):
    page = get_page_or_abort(page_id)

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

    return redirect(url_for('.mod_page', page_id=page_id))
