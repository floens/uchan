from typing import List

from uchan.lib.cache import page_cache
from uchan.lib.model import PageModel
from uchan.lib.repository import pages


def get_page_types() -> 'List[str]':
    return pages.TYPES


def get_all_pages() -> 'List[PageModel]':
    return pages.get_all()


def find_page_id(page_id) -> PageModel:
    return pages.find_by_id(page_id)


# todo: returns an object with a `pages` attribute
def find_front_page():
    return page_cache.find_pages_for_type_cached(pages.TYPE_FRONT_PAGE)


# todo: returns an object with a `pages` attribute
def find_footer_pages():
    return page_cache.find_pages_for_type_cached(pages.TYPE_FOOTER_PAGE)


def get_pages_for_type(page_type: str) -> 'List[PageModel]':
    return pages.find_by_type(page_type)


def get_page_for_link_name(link_name) -> PageModel:
    return pages.find_by_link_name(link_name)


def create_page(page: PageModel):
    pages.create(page)


def delete_page(page: PageModel):
    pages.delete(page)


def update_page(page: PageModel):
    pages.update(page)
