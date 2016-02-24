import json
from time import time

from werkzeug.contrib.cache import MemcachedCache

import config
from uchan.lib.utils import now


def make_attr_dict(value):
    if isinstance(value, list):
        value = [make_attr_dict(i) for i in value]
    elif isinstance(value, dict):
        if not isinstance(value, CacheDict):
            value = CacheDict(value)
        for key in value:
            value[key] = make_attr_dict(value[key])
    return value


class CacheWrapper(MemcachedCache):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set(self, key, value, **kwargs):
        # g.logger.debug('set {} {}'.format(key, value))

        if not super().set(key, json.dumps(value), **kwargs) and config.NO_MEMCACHED_PENALTY:
            raise Exception('Could not set value to cache')

    def get(self, key, convert=False):
        # g.logger.debug('get {}'.format(key))
        res = super().get(key)
        if res is None:
            return None
        else:
            data = json.loads(res)
            if convert:
                return make_attr_dict(data)
            else:
                return data

    def delete(self, key):
        # logger.debug('delete {}'.format(key))
        super().delete(key)

    def _normalize_timeout(self, timeout):
        if timeout is None:
            return self.default_timeout
        # Allow zero to mean the same as does not expire
        if timeout == 0:
            return 0
        return int(time()) + timeout


class CacheDict(dict):
    """
    Makes keys accessible like a property
    """

    def __init__(self, *args, **kwargs):
        try:
            super().__init__(*args, **kwargs)
        except ValueError:
            pass
        self.__dict__ = self

    def convert(self):
        return make_attr_dict(self)


class LocalCache:
    """
    Super simple local cache with no pruning based on a dict.
    Don't do anything special.
    """

    def __init__(self):
        self.items = {}

    def set(self, key, value, timeout=15000):
        self.items[key] = (now() + timeout, value)

    def get(self, key):
        try:
            expires, item = self.items[key]
            if now() < expires:
                return item
        except KeyError:
            pass
        return None


from uchan.lib.cache.board_cache import BoardCache
from uchan.lib.cache.posts_cache import PostsCache
from uchan.lib.cache.site_cache import SiteCache
from uchan.lib.cache.page_cache import PageCache
