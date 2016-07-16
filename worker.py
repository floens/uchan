# Used for development, do not use in production

import sys

import uchan

if __name__ == '__main__':
    uchan.celery.worker_main(sys.argv)
