import json

class UchanConfiguration():
    def __init__(self, parser):
        self.app = AppConfiguration(parser['app'])
        self.http = HttpConfiguration(parser['http'])
        self.file = FileConfiguration(parser['file'])
        self.celery = CeleryConfiguration(parser['celery'])
        self.memcache = MemcacheConfiguration(parser['memcache'])
        self.database = DatabaseConfiguration(parser['database'])


class Configuration():
    def __init__(self, section):
        self.section = section

    def get(self, name, default=None, func=None):
        if func is None:
            func = self.section.get
        value = func(name)
        if value is None:
            if default is None:
                raise Exception(name + ' not present in [' + self.section + ']')
            else:
                value = default
        return value


class AppConfiguration(Configuration):
    def __init__(self, section):
        super().__init__(section)
        self.name = self.get('name')
        self.site_url = self.get('site_url')
        self.debug = self.get('debug', func=section.getboolean, default=False)
        self.enable_cooldown_checking = self.get('enable_cooldown_checking', func=section.getboolean, default=True)
        self.bypass_worker = self.get('bypass_worker', func=section.getboolean, default=False)
        self.manifest = json.loads(self.get('manifest', default='{}'))
        self.thumbnail_op = self.get('thumbnail_op', 256)
        self.thumbnail_reply = self.get('thumbnail_reply', 128)
        self.max_boards_per_moderator = self.get('max_boards_per_moderator', 5)


class HttpConfiguration(Configuration):
    def __init__(self, section):
        super().__init__(section)
        self.use_proxy_fixer = self.get('use_proxy_fixer', func=section.getboolean)
        self.proxy_fixer_num_proxies = self.get('proxy_fixer_num_proxies', func=section.getint)
        self.max_content_length = self.get('max_content_length', func=section.getint)


class FileConfiguration(Configuration):
    def __init__(self, section):
        super().__init__(section)
        self.file_cdn_type = self.get('file_cdn_type')
        self.upload_queue_path = self.get('upload_queue_path')
        self.local_cdn_path = self.get('local_cdn_path')
        self.local_cdn_web_path = self.get('local_cdn_web_path')


class CeleryConfiguration(Configuration):
    def __init__(self, section):
        super().__init__(section)
        self.broker_url = self.get('broker_url')


class MemcacheConfiguration(Configuration):
    def __init__(self, section):
        super().__init__(section)
        self.server = self.get('server')
        self.max_item_size = self.get('max_item_size', func=section.getint)


class DatabaseConfiguration(Configuration):
    def __init__(self, section):
        super().__init__(section)
        self.connect_string = self.get('connect_string')
        self.pool_size = self.get('pool_size', func=section.getint)
        self.echo = self.get('echo', default=False, func=section.getboolean)
