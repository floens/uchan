from typing import List

from sqlalchemy import asc

from uchan.lib import validation
from uchan.lib.cache import cache, cache_key, LocalCache
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

local_cache = LocalCache()


def create(page: PageModel) -> PageModel:
    _validate(page)

    with session() as s:
        existing = s.query(PageOrmModel).filter_by(link_name=page.link_name).one_or_none()
        if existing:
            raise ArgumentError(MESSAGE_PAGE_DUPLICATE_LINK)
        orm_model = page.to_orm_model()
        s.add(orm_model)
        s.flush()
        m = PageModel.from_orm_model(orm_model)

        _cache_page(s, m)

        s.commit()
        return m


def update(page: PageModel):
    _validate(page)

    with session() as s:
        existing = s.query(PageOrmModel).filter_by(id=page.id).one_or_none()
        if not existing:
            raise ArgumentError(MESSAGE_PAGE_NOT_FOUND)
        s.merge(page.to_orm_model())

        _cache_page(s, page)

        s.commit()


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

    lc = local_cache.get(cache_key('type', page_type))
    if lc:
        return list(map(lambda i: i.copy(), lc))

    pages_by_type_cached = cache.get(cache_key('pages_by_type', page_type))
    if pages_by_type_cached is not None:
        res = list(map(lambda i: PageModel.from_cache(i), pages_by_type_cached))
    else:
        with session() as s:
            q = s.query(PageOrmModel).filter_by(type=page_type)
            q = q.order_by(asc(PageOrmModel.order))
            res = list(map(lambda i: PageModel.from_orm_model(i), q.all()))

            cache.set(cache_key('pages_by_type', page_type), list(map(lambda i: i.to_cache(), res)))

            s.commit()

    local_cache.set(cache_key('type', page_type), res)

    return res


def find_by_link_name(link_name: str) -> PageModel:
    lc = local_cache.get(cache_key('link_name', link_name))
    if lc:
        return lc.copy()

    page_cached = cache.get(cache_key('page_by_link_name', link_name))
    if page_cached:
        return PageModel.from_cache(page_cached)
    else:
        with session() as s:
            m = s.query(PageOrmModel).filter_by(link_name=link_name).one_or_none()
            res = None
            if m:
                res = PageModel.from_orm_model(m)

                cache.set(cache_key('page_by_link_name', res.link_name), res.to_cache())

    if res:
        local_cache.set(cache_key('link_name', link_name), res)

    return res


def delete(page: PageModel):
    with session() as s:
        m = s.query(PageOrmModel).filter_by(id=page.id).one()
        s.delete(m)
        s.flush()

        cache.delete(cache_key('page_by_link_name', page.link_name))
        _cache_pages_by_type(s, page.type)

        s.commit()


def _cache_page(s, page: PageModel):
    cache.set(cache_key('page_by_link_name', page.link_name), page.to_cache())
    _cache_pages_by_type(s, page.type)


def _cache_pages_by_type(s, page_type):
    type_pages_q = s.query(PageOrmModel).filter_by(type=page_type).all()
    type_pages = list(map(lambda i: PageModel.from_orm_model(i).to_cache(), type_pages_q))
    cache.set(cache_key('pages_by_type', page_type), type_pages)


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


def _check_page_type(page_type):
    if page_type not in TYPES:
        raise ArgumentError(MESSAGE_PAGE_INVALID_TYPE)
