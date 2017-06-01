from flask import request, redirect, url_for, render_template, flash, abort
from wtforms import StringField, SubmitField, SelectField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange

from uchan.lib import roles, validation
from uchan.lib.exceptions import ArgumentError
from uchan.lib.model import PageModel
from uchan.lib.service import page_service
from uchan.view import with_token
from uchan.view.form import CSRFForm
from uchan.view.form.validators import PageTitleValidator
from uchan.view.mod import mod, mod_role_restrict


class AddPageForm(CSRFForm):
    name = 'Add page'
    action = '.mod_pages'

    title = StringField('Title', [DataRequired(), Length(max=validation.TITLE_MAX_LENGTH)])
    link = StringField('Link name', [DataRequired(), PageTitleValidator()])

    type = SelectField()

    submit = SubmitField('Create page')


class ModifyPageForm(CSRFForm):
    name = 'Update page'

    title = StringField('Title', [DataRequired(), Length(max=validation.TITLE_MAX_LENGTH)])
    order = IntegerField('Order', [NumberRange(min=0)], default=0, description='Order of the page, where applicable')
    content = TextAreaField('Content', [Length(max=validation.CONTENT_MAX_LENGTH)], default='',
                            description='Text contents of the page. This supports post-like formatting.',
                            render_kw={'rows': 30, 'cols': 120})

    submit = SubmitField('Update page')


@mod.route('/mod_page', methods=['GET', 'POST'])
@mod_role_restrict(roles.ROLE_ADMIN)
def mod_pages():
    pages = page_service.get_all_pages()
    page_types = page_service.get_page_types()

    add_page_form = AddPageForm(request.form)
    # TODO: proper page name types
    add_page_form.type.choices = [(i, i) for i in page_types]

    add_page_messages = []

    if request.method == 'POST' and add_page_form.validate():
        title = add_page_form.title.data
        link_name = add_page_form.link.data
        page_type = add_page_form.type.data

        page = PageModel.from_title_link_type(title, link_name, page_type)

        try:
            page = page_service.create_page(page)
            flash('Page created')
            return redirect(url_for('.mod_page', page=page))
        except ArgumentError as e:
            add_page_messages.append(e.message)

    return render_template('mod_pages.html', pages=pages, page_types=page_types, add_page_form=add_page_form,
                           add_page_messages=add_page_messages)


@mod.route('/mod_page/<page:page>', methods=['GET', 'POST'])
@mod_role_restrict(roles.ROLE_ADMIN)
def mod_page(page: PageModel):
    modify_page_form = None

    modify_page_messages = []

    if request.method == 'POST':
        modify_page_form = ModifyPageForm(request.form)
        if modify_page_form.validate():
            page.title = modify_page_form.title.data
            page.content = modify_page_form.content.data
            page.order = modify_page_form.order.data

            try:
                page_service.update_page(page)
                modify_page_messages.append('Page updated')
            except ArgumentError as e:
                modify_page_messages.append(e.message)

    if not modify_page_form:
        modify_page_form = ModifyPageForm(title=page.title, order=page.order, content=page.content)

    modify_page_form.action_url = url_for('.mod_page', page=page)

    return render_template('mod_page.html', page=page, modify_page_form=modify_page_form,
                           modify_page_messages=modify_page_messages)


@mod.route('/mod_page/delete', methods=['POST'])
@mod_role_restrict(roles.ROLE_ADMIN)
@with_token()
def mod_page_delete():
    page = page_service.find_page_id(request.form.get('page_id', type=int))
    if not page:
        abort(404)

    try:
        page_service.delete_page(page)
        flash('Page deleted')
    except ArgumentError as e:
        flash(e.message)

    return redirect(url_for('.mod_pages'))
