import json
from time import time

from uchan import configuration, logger
from uchan.lib.utils import now
from werkzeug.contrib.cache import MemcachedCache


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
    def __init__(self, server, max_item_size):
        super().__init__([server])
        self.client = self._client
        self.client.server_max_value_length = self.max_length = max_item_size

    def set(self, key, value, **kwargs):
        # g.logger.debug('set {} {}'.format(key, value))

        json_data = json.dumps(value, separators=(',', ':'))

        if len(json_data) > self.max_length:
            logger.error('cache value exceeds max length ({} > {})'.format(len(json_data), self.max_length))
            return False

        percentage = len(json_data) / self.max_length
        if percentage > 0.5:
            logger.warning(
                'key {0} exceeds 50% of the total storage available ({1:.2f}%)'.format(key, percentage * 100))

        ret = super().set(key, json_data, **kwargs)
        if not ret:
            logger.error('cache set failed {}'.format(ret))
        return bool(ret)

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


def cache_key(*args):
    # TODO: should we throw an exception on invalid params, to avoid duplicates?
    return ':'.join(map(lambda i: str(i).replace(':', '_'), args))


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


cache = CacheWrapper(configuration.memcache.server, configuration.memcache.max_item_size)
