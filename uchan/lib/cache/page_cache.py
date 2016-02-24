from uchan import g
from uchan.filter.app_filters import page_formatting
from uchan.lib.cache import CacheDict, LocalCache


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


class PageCache:
    def __init__(self, cache):
        self.cache = cache
        self.local_cache = LocalCache()

    def find_page_cached(self, link_name):
        key = self.get_page_key(link_name)

        local_cached = self.local_cache.get(key)
        if local_cached is not None:
            return local_cached

        page_cache = self.cache.get(key, True)
        if page_cache is None:
            page_cache = self.invalidate_page_cache(link_name)

        if page_cache is not None:
            self.local_cache.set(key, page_cache)

        return page_cache

    def get_page_key(self, link_name):
        return 'page_single_{}'.format(link_name)

    def invalidate_page_cache(self, link_name):
        page = g.page_service.get_page_for_link_name(link_name)
        if not page:
            return None
        page_cache = PageCacheProxy(page)
        self.cache.set(self.get_page_key(link_name), page_cache, timeout=0)
        return page_cache

    def find_pages_for_type_cached(self, page_type):
        key = self.get_pages_type_key(page_type)

        local_cached = self.local_cache.get(key)
        if local_cached is not None:
            return local_cached

        pages_cache = self.cache.get(key, True)
        if not pages_cache:
            pages_cache = self.invalidate_pages_with_type(page_type)

        if pages_cache is not None:
            self.local_cache.set(key, pages_cache)

        return pages_cache

    def get_pages_type_key(self, page_type):
        return 'page_type_{}'.format(page_type)

    def invalidate_pages_with_type(self, page_type):
        pages = g.page_service.get_pages_for_type(page_type)
        if pages is None:
            return None
        pages_cache = PagesCacheProxy(pages)
        self.cache.set(self.get_pages_type_key(page_type), pages_cache, timeout=0)
        return pages_cache
