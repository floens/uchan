import click
from sqlalchemy import inspect

from uchan import app
from uchan.lib import roles
from uchan.lib.database import (
    create_all_tables_and_alembic_version_table,
    get_sqlalchemy_engine,
)
from uchan.lib.model import ModeratorModel, PageModel
from uchan.lib.repository import moderators, pages
from uchan.lib.service import moderator_service, page_service


@app.cli.command("createdb")
@click.option("--create-default-mod/--no-create-default-mod", default=True)
@click.option("--skip-exists/--no-skip-exists", default=False)
def createdb(create_default_mod: bool, skip_exists: bool):
    print("* Creating database schema")

    if skip_exists:
        tables = inspect(get_sqlalchemy_engine()).get_table_names()
        if "alembic_version" in tables:
            print("+ Not creating schema: alembic_version already exist")
            return

    # Create the database schema
    create_all_tables_and_alembic_version_table()

    front_page = page_service.find_pages_for_type(pages.TYPE_FRONT_PAGE)
    if not front_page:
        front_page = PageModel.from_title_link_type(
            "Front page", "front_page", pages.TYPE_FRONT_PAGE
        )
        front_page = page_service.create_page(front_page)

        text = (
            "###Setup complete!\nNext, go to the [login page](/mod/auth) to "
            "create your first board.\n"
            "You can now login at the moderation portal "
            "with the default credentials (username 'admin' and password 'password')"
        )

        front_page.content = text
        page_service.update_page(front_page)

    if create_default_mod:
        username = "admin"
        password = "password"

        moderators_exist = len(moderator_service.get_all_moderators()) > 0
        if not moderators_exist:
            moderator = ModeratorModel.from_username(username)
            moderator.roles = [roles.ROLE_ADMIN]
            moderators.create_with_password(moderator, password)
        else:
            print("Moderator already exists")

    print(
        "First-time setup complete! You can now login at the moderation portal "
        "with the default credentials (username 'admin' and password 'password')."
    )
