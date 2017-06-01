from getpass import getpass

from uchan.lib.model import ModeratorModel
from uchan.lib.repository import moderators, pages
from uchan.lib.service import moderator_service, config_service


def init_models():
    from uchan.lib.service import page_service
    from uchan.lib.ormmodel import PageOrmModel
    front_page = page_service.find_pages_for_type(pages.TYPE_FRONT_PAGE)
    if not front_page:
        front_page = PageOrmModel()
        front_page.title = 'Front page'
        front_page.link_name = 'front_page'
        front_page.type = pages.TYPE_FRONT_PAGE
        front_page.order = 0
        front_page.content = 'This is the front page.'
        page_service.create_page(front_page)

    from uchan.lib import roles

    print('Creating a new moderator')
    username = input('username: ')

    existing_moderator = moderator_service.find_moderator_username(username)
    if not existing_moderator:
        password = getpass('password (min 6 chars): ')

        moderator = ModeratorModel.from_username(username)
        moderator.roles = [roles.ROLE_ADMIN]
        moderators.create_with_password(moderator, password)
    else:
        print('Moderator already exists')

    print('Success! You can now login at /mod/auth')


if __name__ == '__main__':
    init_models()
