from uchan import g
from uchan.lib.cache import CacheDict, LocalCache
from uchan.lib.configs import SiteConfig


class SiteCache:
    def __init__(self, cache):
        self.cache = cache
        self.local_cache = LocalCache()

    def find_site_config_cached(self):
        key = 'config_site'

        local_cached = self.local_cache.get(key)
        if local_cached is not None:
            return local_cached

        site_config_cache = self.cache.get(key, True)
        if site_config_cache is None:
            site_config = g.config_service.get_config_by_type(SiteConfig.TYPE)
            site_config_cache = CacheDict(g.config_service.load_config_dict(site_config)).convert()

            self.cache.set(key, site_config_cache, timeout=0)

        if site_config_cache is not None:
            self.local_cache.set(key, site_config_cache)

        return site_config_cache

    def invalidate_site_config(self):
        self.cache.delete('config_site')
