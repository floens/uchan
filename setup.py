from getpass import getpass

from uchan.lib.service import moderator_service, config_service


def init_models():
    from uchan.lib.configs import SiteConfig

    if config_service.get_config_by_type(SiteConfig.TYPE) is None:
        config_service.save_config(SiteConfig(), None)

    from uchan.lib.service import page_service
    from uchan.lib.models import Page
    front_page = page_service.get_pages_for_type(page_service.TYPE_FRONT_PAGE)
    if not front_page:
        front_page = Page()
        front_page.title = 'Front page'
        front_page.link_name = 'front_page'
        front_page.type = page_service.TYPE_FRONT_PAGE
        front_page.order = 0
        front_page.content = 'This is the front page.'
        page_service.create_page(front_page)

    from uchan.lib import roles
    from uchan.lib.models import Moderator

    print('Creating a new moderator')
    username = input('username: ')

    existing_moderator = moderator_service.find_moderator_username(username)
    if not existing_moderator:
        moderator = Moderator()
        moderator.roles = [roles.ROLE_ADMIN]
        moderator.username = username
        password = getpass('password (min 6 chars): ')
        moderator_service.create_moderator(moderator, password)
    else:
        print('Moderator already exists')

    print('Success! You can now login at /mod/auth')


if __name__ == '__main__':
    init_models()
