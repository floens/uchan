import json


class CacheWrapper:
    def __init__(self, cache):
        self.cache = cache

    def set(self, key, value, **kwargs):
        # g.logger.debug('set {} {}'.format(key, value))

        self.cache.set(key, json.dumps(value), **kwargs)

    def get(self, key, convert=False):
        # g.logger.debug('get {}'.format(key))
        res = self.cache.get(key)
        if res is None:
            return None
        else:
            data = json.loads(res)
            if convert:
                return self.make_attr_dict(data)
            else:
                return data

    def make_attr_dict(self, value):
        value = CacheDict(value)
        for key in value:
            if isinstance(value[key], dict):
                value[key] = self.make_attr_dict(value[key])
        return value

    def delete(self, key):
        # logger.debug('delete {}'.format(key))
        self.cache.delete(key)


class CacheDict(dict):
    """
    Makes keys accessible like a property
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self


from unichan.lib.cache.board_cache import BoardCache
from unichan.lib.cache.posts_cache import PostsCache
from unichan.lib.cache.site_cache import SiteCache
