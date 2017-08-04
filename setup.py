def init_models():
    from getpass import getpass

    from uchan.lib.model import ModeratorModel
    from uchan.lib.repository import moderators, pages
    from uchan.lib.service import moderator_service, page_service
    from uchan.lib.model import PageModel
    from uchan.lib import roles

    front_page = page_service.find_pages_for_type(pages.TYPE_FRONT_PAGE)
    if not front_page:
        front_page = PageModel.from_title_link_type('Front page', 'front_page', pages.TYPE_FRONT_PAGE)
        front_page = page_service.create_page(front_page)

        text = '###Setup complete!\nNext, go to the [login page](/mod/auth) to create your first board.'

        front_page.content = text
        page_service.update_page(front_page)

    answer = input('Create a new moderator? [Y/n] ')

    if not answer or answer.lower().startswith('y'):
        while True:
            print('Creating a new moderator')
            username = input('username: ')

            existing_moderator = moderator_service.find_moderator_username(username)
            if not existing_moderator:
                password = getpass('password (min 6 chars): ')

                moderator = ModeratorModel.from_username(username)
                moderator.roles = [roles.ROLE_ADMIN]
                moderators.create_with_password(moderator, password)
                break
            else:
                print('Moderator already exists')

    print('First-time setup complete! You can now login at /mod/auth')


if __name__ == '__main__':
    init_models()
