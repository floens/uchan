ROLE_ADMIN = 'admin'

ALL_ROLES = [ROLE_ADMIN]


def get_role_name(roles):
    if ROLE_ADMIN in roles:
        return 'Admin'
    raise Exception('Unknown roles')


BOARD_ROLE_JANITOR = 'janitor'
BOARD_ROLE_MODERATOR = 'mod'
BOARD_ROLE_CREATOR = 'creator'

ALL_BOARD_ROLES = [BOARD_ROLE_JANITOR, BOARD_ROLE_MODERATOR, BOARD_ROLE_CREATOR]
