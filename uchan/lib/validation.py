import string

USERNAME_MIN_LENGTH = 1
USERNAME_MAX_LENGTH = 50
USERNAME_ALLOWED_CHARS = string.ascii_letters + string.digits + '_'
PASSWORD_MIN_LENGTH = 6
PASSWORD_MAX_LENGTH = 255


def check_username_validity(username):
    if username is None or len(username) < USERNAME_MIN_LENGTH or len(username) >= USERNAME_MAX_LENGTH:
        return False

    if not all(c in USERNAME_ALLOWED_CHARS for c in username):
        return False

    return True


def check_password_validity(password):
    if password is None or len(password) < PASSWORD_MIN_LENGTH or len(password) >= PASSWORD_MAX_LENGTH:
        return False

    return True


BOARD_NAME_MAX_LENGTH = 20
BOARD_NAME_ALLOWED_CHARS = string.ascii_lowercase + string.digits + '_'

DISALLOWED_BOARD_NAMES = [
    # Names that are routes now
    'mod', 'post_manage', 'banned', 'post', 'api', 'find_post', 'static', 'page', 'verify',
    # names that can be confusing
    'admin', 'ban', 'bans', 'id', 'moderate', 'auth', 'login', 'logout', 'res', 'thread', 'threads',
    'board', 'boards', 'report', 'reports', 'user', 'users', 'log', 'logs', 'search', 'config', 'debug', 'create',
    'delete', 'update', 'faq', 'index', 'read', 'all'
]


def check_board_name_validity(name):
    if not 0 < len(name) <= BOARD_NAME_MAX_LENGTH:
        return False

    if not all(c in BOARD_NAME_ALLOWED_CHARS for c in name):
        return False

    if name in DISALLOWED_BOARD_NAMES:
        return False

    return True


TITLE_MAX_LENGTH = 20
CONTENT_MAX_LENGTH = 10000
LINK_NAME_MAX_LENGTH = 20
LINK_NAME_ALLOWED_CHARS = string.ascii_letters + string.digits + '_'


def check_page_title_validity(title):
    if not 0 < len(title) <= TITLE_MAX_LENGTH:
        return False

    return True


def check_page_link_name_validity(name):
    if not 0 < len(name) <= LINK_NAME_MAX_LENGTH:
        return False

    if not all(c in LINK_NAME_ALLOWED_CHARS for c in name):
        return False

    return True


def check_page_content_validity(content):
    if len(content) > CONTENT_MAX_LENGTH:
        return False

    return True

MAX_FILES = 20
