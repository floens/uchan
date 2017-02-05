import string

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

TYPE_FRONT_PAGE = 'front_page'
TYPE_FOOTER_PAGE = 'footer_page'

TYPES = [TYPE_FOOTER_PAGE, TYPE_FRONT_PAGE]

TITLE_MAX_LENGTH = 20
CONTENT_MAX_LENGTH = 10000
LINK_NAME_MAX_LENGTH = 20
LINK_NAME_ALLOWED_CHARS = string.ascii_letters + string.digits + '_'

from uchan.lib.exceptions import ArgumentError
from uchan.lib.cache import page_cache
from uchan.lib.database import get_db
from uchan.lib.models import Page


def check_title_validity(title):
    if not 0 < len(title) <= TITLE_MAX_LENGTH:
        return False

    return True


def check_link_name_validity(name):
    if not 0 < len(name) <= LINK_NAME_MAX_LENGTH:
        return False

    if not all(c in LINK_NAME_ALLOWED_CHARS for c in name):
        return False

    return True


def check_page_type(type):
    return type in TYPES


def check_content_validity(content):
    if len(content) > CONTENT_MAX_LENGTH:
        return False

    return True


def get_page_types():
    return TYPES


def get_all_pages():
    db = get_db()
    return db.query(Page).all()


def get_pages_for_type(type):
    db = get_db()
    return db.query(Page).filter_by(type=type).order_by(Page.order).all()


def get_page_for_link_name(link_name):
    db = get_db()

    try:
        return db.query(Page).filter_by(link_name=link_name).one()
    except NoResultFound:
        return None


def create_page(page):
    if not check_page_type(page.type):
        raise ArgumentError('Invalid page type')

    if not check_title_validity(page.title):
        raise ArgumentError('Invalid page title')

    if not check_link_name_validity(page.link_name):
        raise ArgumentError('Invalid page link')

    db = get_db()
    db.add(page)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise ArgumentError('Duplicate link name')

    page_cache.invalidate_pages_with_type(page.type)


def delete_page(page):
    db = get_db()
    db.delete(page)
    db.commit()

    page_cache.invalidate_page_cache(page.link_name)
    page_cache.invalidate_pages_with_type(page.type)


def update_page(page):
    db = get_db()

    if not check_title_validity(page.title):
        raise ArgumentError('Invalid page title')

    if not check_content_validity(page.content):
        raise ArgumentError('Invalid page content')

    if page.order < 0 or page.order > 1000:
        raise ArgumentError('Invalid page order')

    db.merge(page)
    db.commit()

    page_cache.invalidate_page_cache(page.link_name)
    page_cache.invalidate_pages_with_type(page.type)


def find_page_id(id):
    db = get_db()
    try:
        return db.query(Page).filter_by(id=id).one()
    except NoResultFound:
        return None
