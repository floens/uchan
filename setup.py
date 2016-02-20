from getpass import getpass


def init_models():
    from unichan import database

    database.metadata_create_all()

    from unichan import g

    from unichan.lib.configs import SiteConfig

    if g.config_service.get_config_by_type(SiteConfig.TYPE) is None:
        g.config_service.save_config(SiteConfig(), None)

    from unichan.lib.models import Board
    b_board = g.board_service.find_board('a')
    if not b_board:
        a_board = Board()
        a_board.name = 'a'
        g.board_service.add_board(a_board)

    from unichan.lib import roles
    from unichan.lib.models import Moderator

    print('Creating a new moderator')
    username = input('username: ')

    existing_moderator = g.moderator_service.find_moderator_username('admin')
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
