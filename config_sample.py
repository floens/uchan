# App
APP_NAME = 'uchan'
SITE_NAME = 'µchan'
SITE_URL = 'http://127.0.0.1'

DEBUG = True

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

# Flask
# Keep this the same as your nginx client_max_body_size config
MAX_CONTENT_LENGTH = 5 * 1024 * 1024

DATABASE_CONNECT_STRING = 'postgresql+psycopg2://postgres:postgres@127.0.0.1:5432/unichan'
DATABASE_POOL_SIZE = 5

# Generate with `import os` `os.urandom(32)`
SECRET_KEY = None
