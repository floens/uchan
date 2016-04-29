ROLE_ADMIN = 'admin'

ALL_ROLES = [ROLE_ADMIN]


def get_role_name(roles):
    if ROLE_ADMIN in roles:
        return 'Admin'
    raise Exception('Unknown roles')


REPORT_ROLE_JANITOR = 'janitor'
REPORT_ROLE_MODERATOR = 'mod'
REPORT_ROLE_CREATOR = 'creator'

ALL_REPORT_ROLES = [REPORT_ROLE_JANITOR, REPORT_ROLE_MODERATOR, REPORT_ROLE_CREATOR]
