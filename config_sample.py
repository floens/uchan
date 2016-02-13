# App
APP_NAME = 'uchan'
SITE_NAME = 'µchan'
SITE_URL = 'http://127.0.0.1'

DEBUG = True

# Flask
DATABASE_CONNECT_STRING = 'postgresql+psycopg2://postgres:postgres@127.0.0.1:5432/unichan'
DATABASE_POOL_SIZE = 5

# Generate with `import os` `os.urandom(32)`
SECRET_KEY = None
