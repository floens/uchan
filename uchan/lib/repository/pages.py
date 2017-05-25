from typing import List

from uchan.lib import validation
from uchan.lib.cache import page_cache
from uchan.lib.database import session
from uchan.lib.exceptions import ArgumentError
from uchan.lib.model import PageModel
from uchan.lib.ormmodel import PageOrmModel

TYPE_FRONT_PAGE = 'front_page'
TYPE_FOOTER_PAGE = 'footer_page'

TYPES = [TYPE_FOOTER_PAGE, TYPE_FRONT_PAGE]

MESSAGE_PAGE_NOT_FOUND = 'Page not found'
MESSAGE_PAGE_INVALID_TYPE = 'Invalid page type'
MESSAGE_PAGE_INVALID_TITLE = 'Invalid page title'
MESSAGE_PAGE_INVALID_CONTENT = 'Invalid page content'
MESSAGE_PAGE_INVALID_ORDER = 'Invalid page order'
MESSAGE_PAGE_INVALID_LINK = 'Invalid page link'
MESSAGE_PAGE_DUPLICATE_LINK = 'Duplicate link name'


def create(page: PageModel):
    _validate(page)

    with session() as s:
        existing = s.query(PageOrmModel).filter_by(link_name=page.link_name).one_or_none()
        if existing:
            raise ArgumentError(MESSAGE_PAGE_DUPLICATE_LINK)
        s.add(page.to_orm_model())
        s.commit()


def update(page: PageModel):
    _validate(page)

    with session() as s:
        existing = s.query(PageOrmModel).filter_by(id=page.id).one_or_none()
        if not existing:
            raise ArgumentError(MESSAGE_PAGE_NOT_FOUND)
        s.merge(page.to_orm_model())
        s.commit()

    page_cache.invalidate_page_cache(page.link_name)
    page_cache.invalidate_pages_with_type(page.type)


def _validate(page: PageModel):
    _check_page_type(page.type)

    if not validation.check_page_title_validity(page.title):
        raise ArgumentError(MESSAGE_PAGE_INVALID_TITLE)

    if not validation.check_page_link_name_validity(page.link_name):
        raise ArgumentError(MESSAGE_PAGE_INVALID_LINK)

    if not validation.check_page_content_validity(page.content):
        raise ArgumentError(MESSAGE_PAGE_INVALID_CONTENT)

    if page.order < 0 or page.order > 1000:
        raise ArgumentError(MESSAGE_PAGE_INVALID_ORDER)


def get_all() -> 'List[PageModel]':
    with session() as s:
        q = s.query(PageOrmModel)
        res = list(map(lambda i: PageModel.from_orm_model(i), q.all()))
        s.commit()
        return res


def find_by_id(page_id: int) -> PageModel:
    with session() as s:
        m = s.query(PageOrmModel).filter_by(id=page_id).one_or_none()
        res = None
        if m:
            res = PageModel.from_orm_model(m)
        return res


def find_by_type(page_type: str) -> 'List[PageModel]':
    _check_page_type(page_type)

    with session() as s:
        q = s.query(PageOrmModel).filter_by(type=page_type)
        res = list(map(lambda i: PageModel.from_orm_model(i), q.all()))
        s.commit()
        return res


def find_by_link_name(link_name: str) -> PageModel:
    with session() as s:
        m = s.query(PageOrmModel).filter_by(link_name=link_name).one_or_none()
        res = None
        if m:
            res = PageModel.from_orm_model(m)
        return res


def _check_page_type(page_type):
    if page_type not in TYPES:
        raise ArgumentError(MESSAGE_PAGE_INVALID_TYPE)


def delete(page: PageModel):
    with session() as s:
        m = s.query(PageOrmModel).filter_by(id=page.id).one()
        s.delete(m)
        s.commit()

    page_cache.invalidate_page_cache(page.link_name)
    page_cache.invalidate_pages_with_type(page.type)
