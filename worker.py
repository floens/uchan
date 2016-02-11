import sys

import unichan

if __name__ == '__main__':
    unichan.celery.worker_main(sys.argv)
