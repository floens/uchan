import string

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from uchan.database import get_db
from uchan.lib import ArgumentError
from uchan.lib.models import Page


class PageService:
    TYPE_FRONT_PAGE = 'front_page'
    TYPE_FOOTER_PAGE = 'footer_page'

    TYPES = [TYPE_FRONT_PAGE, TYPE_FOOTER_PAGE]

    TITLE_MAX_LENGTH = 20
    CONTENT_MAX_LENGTH = 10000
    LINK_NAME_MAX_LENGTH = 20
    LINK_NAME_ALLOWED_CHARS = string.ascii_letters + string.digits + '_'

    def __init__(self, cache):
        self.cache = cache

    def check_title_validity(self, title):
        if not 0 < len(title) <= self.TITLE_MAX_LENGTH:
            return False

        return True

    def check_link_name_validity(self, name):
        if not 0 < len(name) <= self.LINK_NAME_MAX_LENGTH:
            return False

        if not all(c in self.LINK_NAME_ALLOWED_CHARS for c in name):
            return False

        return True

    def check_page_type(self, type):
        return type in self.TYPES

    def check_content_validity(self, content):
        if len(content) > self.CONTENT_MAX_LENGTH:
            return False

        return True

    def get_page_types(self):
        return self.TYPES

    def get_all_pages(self):
        db = get_db()
        return db.query(Page).all()

    def get_pages_for_type(self, type):
        db = get_db()
        return db.query(Page).filter_by(type=type).order_by(Page.order).all()

    def get_page_for_type(self, type):
        pages = self.get_pages_for_type(type)
        return pages[0] if pages else None

    def get_page_for_link_name(self, link_name):
        db = get_db()

        try:
            return db.query(Page).filter_by(link_name=link_name).one()
        except NoResultFound:
            return None

    def create_page(self, page):
        if not self.check_page_type(page.type):
            raise ArgumentError('Invalid page type')

        if not self.check_title_validity(page.title):
            raise ArgumentError('Invalid page title')

        if not self.check_link_name_validity(page.link_name):
            raise ArgumentError('Invalid page link')

        db = get_db()
        db.add(page)
        try:
            db.commit()
        except IntegrityError as e:
            db.rollback()
            raise ArgumentError('Duplicate link name')

    def delete_page(self, page):
        db = get_db()
        db.delete(page)
        db.commit()

    def update_page(self, page):
        db = get_db()

        if not self.check_title_validity(page.title):
            raise ArgumentError('Invalid page title')

        if not self.check_content_validity(page.content):
            raise ArgumentError('Invalid page content')

        if page.order < 0 or page.order > 1000:
            raise ArgumentError('Invalid page order')

        db.merge(page)
        db.commit()

    def find_page_id(self, id):
        db = get_db()
        try:
            return db.query(Page).filter_by(id=id).one()
        except NoResultFound:
            return None
