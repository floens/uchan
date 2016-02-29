ROLE_ADMIN = 'admin'

ALL_ROLES = [ROLE_ADMIN]


def get_role_name(roles):
    if ROLE_ADMIN in roles:
        return 'Admin'
    raise Exception('Unknown roles')
