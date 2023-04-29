from concurrent import futures
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

import requests
from requests import RequestException

from uchan import config, logger
from uchan.lib.model import BoardModel, ThreadModel

# TODO: We can't use url_for outside the flask context, until there's a better way, use
# this
VIEW_BOARD_URL = "/{}/"
VIEW_BOARD_URL_PAGE = "/{}/{}"
VIEW_THREAD_URL = "/{}/read/{}"
VIEW_CATALOG_URL = "/{}/catalog"

API_CATALOG_URL = "/api/catalog/{}"
API_THREAD_URL = "/api/thread/{}/{}"


def purge_board(board: BoardModel):
    _purge(VIEW_BOARD_URL.format(board.name))
    for page in range(1, board.config.pages + 1):
        _purge(VIEW_BOARD_URL_PAGE.format(board.name, page))
    _purge(VIEW_CATALOG_URL.format(board.name))
    _purge(API_CATALOG_URL.format(board.name))


def purge_thread(board: BoardModel, thread: ThreadModel, wait=False):
    api_future = _purge(API_THREAD_URL.format(board.name, thread.refno))
    thread_future = _purge(VIEW_THREAD_URL.format(board.name, thread.refno))
    if wait and api_future and thread_future:
        futures.wait([api_future, thread_future])


_pool = ThreadPoolExecutor(4)


def _purge(endpoint):
    if config.varnish_enable_purging:
        url = config.varnish_url + endpoint

        return _pool.submit(_call_purge, url)


def _call_purge(url):
    host = urlparse(config.site_url).netloc

    try:
        res = requests.request(
            "PURGE", url, headers={"Host": host, "User-Agent": "app"}, timeout=1.0
        )
        res.raise_for_status()
    except RequestException:
        logger.error('Failed to purge "{}"'.format(url), exc_info=True)
