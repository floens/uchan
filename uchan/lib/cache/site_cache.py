from uchan.lib.cache import cache, CacheDict, LocalCache
from uchan.lib.configs import SiteConfig
from uchan.lib.service import config_service

local_cache = LocalCache()


def find_site_config():
    key = 'config_site'

    local_cached = local_cache.get(key)
    if local_cached is not None:
        return local_cached

    site_config_cache = cache.get(key, True)
    if site_config_cache is None:
        site_config = config_service.get_config_by_type(SiteConfig.TYPE)
        site_config_cache = CacheDict(config_service.load_config_dict(site_config)).convert()

        cache.set(key, site_config_cache, timeout=0)

    site_config = SiteConfig()
    site_config.set_values_from_cache(site_config_cache)

    local_cache.set(key, site_config)

    return site_config


def invalidate_site_config():
    cache.delete('config_site')
