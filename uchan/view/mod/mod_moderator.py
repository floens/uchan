from flask import abort, flash, redirect, render_template, request, url_for
from wtforms import HiddenField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired

from uchan.lib import roles, validation
from uchan.lib.exceptions import ArgumentError
from uchan.lib.mod_log import mod_log
from uchan.lib.model import ModeratorModel
from uchan.lib.moderator_request import request_moderator
from uchan.lib.service import board_service, moderator_service
from uchan.view import with_token
from uchan.view.form import CSRFForm
from uchan.view.form.validators import (
    BoardValidator,
    ModeratorPasswordValidator,
    ModeratorUsernameValidator,
)
from uchan.view.mod import mod, mod_role_restrict


class AddModeratorForm(CSRFForm):
    name = "Create new moderator"
    action = ".mod_moderators"

    username = StringField(
        "Username",
        [DataRequired(), ModeratorUsernameValidator()],
        description="Username of the moderator",
    )
    password = PasswordField("Password", [DataRequired(), ModeratorPasswordValidator()])
    submit = SubmitField("Create moderator")


class AddModeratorBoardForm(CSRFForm):
    name = "Assign board to moderator"
    action = ".mod_moderator"
    board_add = (
        HiddenField()
    )  # Used to differentiate between the different forms on the page

    board = StringField(
        "Board name",
        [DataRequired(), BoardValidator()],
        description="Name of the board",
    )
    submit = SubmitField("Assign")


@mod.route("/mod_moderator", methods=["GET", "POST"])
@mod_role_restrict(roles.ROLE_ADMIN)
def mod_moderators():
    add_moderator_form = AddModeratorForm(request.form)
    if request.method == "POST" and add_moderator_form.validate():
        try:
            moderator = moderator_service.user_register(
                add_moderator_form.username.data,
                add_moderator_form.password.data,
                add_moderator_form.password.data,
            )
            flash("Moderator created")
            mod_log(
                "moderator add {} username {}".format(moderator.id, moderator.username)
            )
        except ArgumentError as e:
            flash(e.message)

    all_moderators = moderator_service.get_all_moderators(include_boards=True)

    return render_template(
        "mod_moderators.html",
        add_moderator_form=add_moderator_form,
        moderators=all_moderators,
    )


@mod.route("/mod_moderator/delete", methods=["POST"])
@mod_role_restrict(roles.ROLE_ADMIN)
@with_token()
def mod_moderator_delete():
    moderator = moderator_service.find_moderator_id(
        request.form.get("moderator_id", type=int)
    )
    username = moderator.username

    authed_moderator = request_moderator()
    self_delete = authed_moderator == moderator

    # moderator_service.delete_moderator(moderator)
    # if self_delete:
    #    unset_mod_authed()
    flash("Moderator deleted")
    mod_log(
        "moderator delete username {}".format(username),
        moderator_name=authed_moderator.username,
    )

    if self_delete:
        return redirect(url_for(".mod_auth"))
    else:
        return redirect(url_for(".mod_moderators"))


@mod.route("/mod_moderator/<moderator:moderator>", methods=["GET", "POST"])
@mod_role_restrict(roles.ROLE_ADMIN)
def mod_moderator(moderator: ModeratorModel):
    all_roles = ", ".join(roles.ALL_ROLES)
    all_board_roles = ", ".join(roles.ALL_BOARD_ROLES)

    add_moderator_board_form = AddModeratorBoardForm(request.form)
    add_moderator_board_form.action_url = url_for(".mod_moderator", moderator=moderator)
    if (
        request.method == "POST"
        and request.form.get("board_add") is not None
        and add_moderator_board_form.validate()
    ):
        try:
            board = board_service.find_board(add_moderator_board_form.board.data)
            board_service.add_moderator(board, moderator)
            flash("Assigned " + board.name)
            mod_log("add board to {} /{}/".format(moderator.username, board.name))
        except ArgumentError as e:
            flash(e.message)

    if request.method == "POST" and request.form.get("board_remove"):
        # HTML checkboxes are fun!
        board_names_to_remove = request.form.getlist("board_remove")
        boards_to_remove = []
        for board_name in board_names_to_remove:
            board = board_service.find_board(board_name)
            if not board:
                # we coded the name in the html, can't be an user error
                abort(400)
            boards_to_remove.append(board)

        for board in boards_to_remove:
            try:
                board_service.remove_moderator(board, moderator)
                flash("Revoked " + board.name)
                mod_log(
                    "remove board from {} /{}/".format(moderator.username, board.name)
                )
            except ArgumentError as e:
                flash(e.message)

    if request.method == "POST" and request.form.get("role_remove"):
        pass

    moderating_boards = moderator_service.get_all_moderating_boards(moderator)

    return render_template(
        "mod_moderator.html",
        moderator=moderator,
        moderating_boards=moderating_boards,
        all_roles=all_roles,
        all_board_roles=all_board_roles,
        add_moderator_board_form=add_moderator_board_form,
    )


@mod.route("/mod_moderator/<moderator:moderator>/change_password", methods=["POST"])
@mod_role_restrict(roles.ROLE_ADMIN)
@with_token()
def mod_moderator_password(moderator):
    new_password = request.form["new_password"]

    if not validation.check_password_validity(new_password):
        flash("Invalid password")
        return redirect(url_for(".mod_moderator", moderator_id=moderator.id))

    try:
        moderator_service.set_password(moderator, new_password)
        flash("Changed password")
        mod_log("changed password for {}".format(moderator.username))
    except ArgumentError as e:
        flash(e.message)

    return redirect(url_for(".mod_moderator", moderator=moderator))


@mod.route("/mod_moderator/<moderator:moderator>/role_add", methods=["POST"])
@mod_role_restrict(roles.ROLE_ADMIN)
@with_token()
def mod_moderator_role_add(moderator):
    role = request.form["role"]

    if not moderator_service.role_exists(role):
        flash("That role does not exist")
    else:
        try:
            moderator_service.add_role(moderator, role)
            flash("Role added")
            mod_log("add role {} to {}".format(role, moderator.username))
        except ArgumentError as e:
            flash(e.message)

    return redirect(url_for(".mod_moderator", moderator=moderator))


@mod.route("/mod_moderator/<moderator:moderator>/role_remove", methods=["POST"])
@mod_role_restrict(roles.ROLE_ADMIN)
@with_token()
def mod_moderator_role_remove(moderator):
    role = request.form["role"]

    if not moderator_service.role_exists(role):
        flash("That role does not exist")
    else:
        try:
            moderator_service.remove_role(moderator, role)
            flash("Role removed")
            mod_log("remove role {} from {}".format(role, moderator.username))
        except ArgumentError as e:
            flash(e.message)

    return redirect(url_for(".mod_moderator", moderator=moderator))
