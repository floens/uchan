from uchan.filter.app_filters import page_formatting
from uchan.lib.cache import cache, CacheDict, LocalCache
from uchan.lib.service import page_service


class PageCacheProxy(CacheDict):
    def __init__(self, page):
        super().__init__()
        self.title = page.title
        self.link_name = page.link_name
        self.type = page.type
        self.order = page.order
        self.content = page.content
        self.content_html = page_formatting(page.content)


class PagesCacheProxy(CacheDict):
    def __init__(self, pages):
        super().__init__()
        self.pages = [PageCacheProxy(i) for i in pages]


local_cache = LocalCache()


def find_page_cached(link_name):
    key = get_page_key(link_name)

    local_cached = local_cache.get(key)
    if local_cached is not None:
        return local_cached

    page_cache = cache.get(key, True)
    if page_cache is None:
        page_cache = invalidate_page_cache(link_name)

    if page_cache is not None:
        local_cache.set(key, page_cache)

    return page_cache


def get_page_key(link_name):
    return 'page_single${}'.format(link_name)


def invalidate_page_cache(link_name):
    key = get_page_key(link_name)
    page = page_service.get_page_for_link_name(link_name)
    if not page:
        cache.delete(key)
        return None
    page_cache = PageCacheProxy(page)
    cache.set(key, page_cache, timeout=0)
    return page_cache


def find_pages_for_type_cached(page_type):
    key = get_pages_type_key(page_type)

    local_cached = local_cache.get(key)
    if local_cached is not None:
        return local_cached

    pages_cache = cache.get(key, True)
    if not pages_cache:
        pages_cache = invalidate_pages_with_type(page_type)

    if pages_cache is not None:
        local_cache.set(key, pages_cache)

    return pages_cache


def get_pages_type_key(page_type):
    return 'page_type${}'.format(page_type)


def invalidate_pages_with_type(page_type):
    key = get_pages_type_key(page_type)
    pages = page_service.get_pages_for_type(page_type)
    if pages is None:
        cache.delete(key)
        return None
    pages_cache = PagesCacheProxy(pages)
    cache.set(key, pages_cache, timeout=0)
    return pages_cache
