from typing import List

from uchan.lib.mod_log import mod_log
from uchan.lib.model import PageModel
from uchan.lib.repository import pages


def get_page_types() -> List[str]:
    return pages.TYPES


def get_all_pages() -> List[PageModel]:
    return pages.get_all()


def find_page_id(page_id) -> PageModel:
    return pages.find_by_id(page_id)


def find_front_page() -> PageModel:
    p = pages.find_by_type(pages.TYPE_FRONT_PAGE)
    return p[0] if p else None


def find_footer_pages() -> List[PageModel]:
    return pages.find_by_type(pages.TYPE_FOOTER_PAGE)


def find_pages_for_type(page_type: str) -> List[PageModel]:
    return pages.find_by_type(page_type)


def find_page_for_link_name(link_name) -> PageModel:
    return pages.find_by_link_name(link_name)


def create_page(page: PageModel) -> PageModel:
    r = pages.create(page)
    mod_log('page {} created'.format(page.link_name))
    return r


def delete_page(page: PageModel):
    pages.delete(page)
    mod_log('page {} deleted'.format(page.link_name))


def update_page(page: PageModel):
    pages.update(page)
    mod_log('page {} updated'.format(page.link_name))
