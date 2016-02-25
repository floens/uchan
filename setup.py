from getpass import getpass


def init_models():
    from uchan.lib import database

    database.metadata_create_all()

    from uchan import g

    from uchan.lib.configs import SiteConfig

    if g.config_service.get_config_by_type(SiteConfig.TYPE) is None:
        g.config_service.save_config(SiteConfig(), None)

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


if __name__ == '__main__':
    init_models()
