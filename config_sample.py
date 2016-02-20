# App
# For logs and the like
APP_NAME = 'uchan'

# Url the site is reachable at
# This needs to match the referer when posting
SITE_URL = 'http://127.0.0.1'

# Enable flask debugging. NEVER enable on production.
DEBUG = False

# The temporary dir in which files are placed that are received from the client.
# The temporary files will be deleted after a post unless the python process crashes.
UPLOAD_QUEUE_PATH = '/var/tmp/uchan_upload_queue'

# Which cdn type to use, see FileService for more details
# Types available: "local"
FILE_CDN_TYPE = 'local'

# Settings for the local cdn type
# Absolute path of where to place the the files.
LOCAL_CDN_PATH = '/var/www/uchan_media/'
# Absolute base url of where the client should request the file
LOCAL_CDN_WEB_PATH = 'https://cdn.example.com/media/'

# Enable the cooldowns specified in the BanService. Turning off is useful for developing.
ENABLE_COOLDOWN_CHECKING = True

# Memcached servers to use
MEMCACHED_SERVERS = ['127.0.0.1:11211']
# Fail when connecting to the memcached server fails
# Only disable when developing, running without memcached destroys performance.
NO_MEMCACHED_PENALTY = True

# Enable this when serving behind a proxy (almost always)
# Do not use this middleware in non-proxy setups for security reasons.
USE_PROXY_FIXER = True
# The number of proxies this instance is behind
# This needs to be set to prevent ip spoofing by malicious clients appending their own forwarded-for header
# See `werkzeug.contrib.fixers.ProxyFix` for more info.
# Two for a nginx > varnish > uwsgi setup
PROXY_FIXER_NUM_PROXIES = 2

# Keep this the same as your nginx client_max_body_size config
MAX_CONTENT_LENGTH = 5 * 1024 * 1024

DATABASE_CONNECT_STRING = 'postgresql+psycopg2://uchan:uchan@/uchan'
# Check this with your uwsgi total thread count + worker count and the postgres max_connections
DATABASE_POOL_SIZE = 4

# Generate with `import os` `os.urandom(32)`
SECRET_KEY = None
