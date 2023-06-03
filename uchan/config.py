from typing import Literal

from pydantic import AnyHttpUrl, BaseSettings, Json


class UchanConfig(BaseSettings):
    class Config:
        env_file = ".env"

    # postgres_dsn: PostgresDsn = "postgresql+psycopg2://uchan:uchan@db/uchan"
    database_host: str = ""
    database_port: int = 5432
    database_name: str = "uchan"
    database_user: str = "uchan"
    database_password: str = ""

    # Amqp broker url
    # broker_dsn: AmqpDsn = "amqp://queue/"
    broker_host: str = ""
    broker_port: int = 5672
    broker_user: str = "user"
    broker_password: str = ""
    broker_vhost: str = ""

    # Memcache server address
    memcached_host: str = ""
    memcached_port: int = 11211

    # Enable to purge the varnish cache
    varnish_enable_purging: bool = False
    # Address we can reach varnish, to send PURGE requests to.
    varnish_host: str = ""

    # URL where uchan is reachable from. Used for URL generation.
    site_url: AnyHttpUrl = "http://localhost"

    asset_build_directory: str = "build/static"
    asset_build_meta_file: str = "build/static/_meta.json"
    asset_url: str = "http://localhost/static/"
    asset_watch_for_changes: bool = False

    # Content of the manifest.json file
    manifest: Json = '{"name": "uchan"}'

    auth_login_require_captcha: bool = False
    auth_register_require_captcha: bool = True

    enable_cooldown_checking: bool = True
    bypass_worker: bool = False
    thumbnail_op: int = 256
    thumbnail_reply: int = 128
    max_boards_per_moderator: int = 5
    mod_log_path: str = "log/mod.log"

    # Enable this when serving behind a proxy (almost always)
    # Do not use this middleware in non-proxy setups for security reasons.
    use_proxy_fixer: bool = True

    # The number of proxies this instance is behind This needs to be set to prevent ip
    # spoofing by malicious clients appending their own forwarded-for header
    # 2 for a varnish > nginx > uwsgi setup
    # 3 for a front_end > varnish > nginx > uwsgi setup
    proxy_fixer_num_proxies: int = 1

    # Max POST size to accept.
    # Keep this the same as your nginx client_max_body_size config.
    # 5242880 = 5 * 1024 * 1024
    max_content_length: int = 5242880

    # Which cdn type to use, see file_service for more details
    # Types available: "local"
    file_cdn_type: Literal["local"] = "local"

    # The temporary dir in which files are placed that are received from the client. The
    # temporary files will be deleted after a post unless the python process crashes.
    upload_queue_path: str = "mediaqueue"

    # Settings for the local cdn type
    # Absolute path of where to place the files.
    local_cdn_path: str = "media"

    # Base url of where the client should request the file.
    local_cdn_web_path: str = "/media/"

    # Check this with your uwsgi total thread count + worker count and the postgres
    # max_connections
    database_pool_size: int = 4
    database_echo_sql: bool = False

    # The -I flag of memcache, the max size of items
    # note: "-I 2M" means "2 * 1024 * 1024" here
    # Memcache defaults to 1M
    # 1048576 = 1 * 1024 * 1024
    memcache_max_item_size: int = 1048576

    # Get recaptcha keys for your site here
    # https://www.google.com/recaptcha/intro/index.html The following keys are test
    # keys, and do not offer any protection.
    google_captcha2_sitekey: str = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
    google_captcha2_secret: str = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"
