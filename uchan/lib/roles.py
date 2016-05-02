ROLE_ADMIN = 'admin'

ALL_ROLES = [ROLE_ADMIN]


def get_role_name(roles):
    if ROLE_ADMIN in roles:
        return 'Admin'
    raise Exception('Unknown roles')


BOARD_ROLE_CREATOR = 'creator'
BOARD_ROLE_FULL_PERMISSION = 'full_permission'
BOARD_ROLE_JANITOR = 'janitor'
BOARD_ROLE_CONFIG = 'config'

ALL_BOARD_ROLES = [BOARD_ROLE_CREATOR, BOARD_ROLE_FULL_PERMISSION, BOARD_ROLE_JANITOR, BOARD_ROLE_CONFIG]
