from getpass import getpass


def init_models():
    from uchan.lib import database

    database.metadata_create_all()

    from uchan import g

    from uchan.lib.configs import SiteConfig

    if g.config_service.get_config_by_type(SiteConfig.TYPE) is None:
        g.config_service.save_config(SiteConfig(), None)

    from uchan.lib.service import PageService
    from uchan.lib.models import Page
    front_page = g.page_service.get_pages_for_type(PageService.TYPE_FRONT_PAGE)
    if not front_page:
        front_page = Page()
        front_page.title = 'Front page'
        front_page.link_name = 'front_page'
        front_page.type = PageService.TYPE_FRONT_PAGE
        front_page.order = 0
        front_page.content = 'This is the front page.'
        g.page_service.create_page(front_page)

    from uchan.lib import roles
    from uchan.lib.models import Moderator

    print('Creating a new moderator')
    username = input('username: ')

    existing_moderator = g.moderator_service.find_moderator_username(username)
    if not existing_moderator:
        moderator = Moderator()
        moderator.roles = [roles.ROLE_ADMIN]
        moderator.username = username
        password = getpass('password (min 6 chars): ')
        g.moderator_service.create_moderator(moderator, password)
    else:
        print('Moderator already exists')

    print('Success! You can not login at /mod/auth')


if __name__ == '__main__':
    init_models()
