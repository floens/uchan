from concurrent.futures import ThreadPoolExecutor, Future
from urllib.parse import urlparse

import requests
from requests import RequestException

from uchan import logger, configuration
from uchan.lib.model import ThreadModel, BoardModel

# TODO: We can't use url_for outside the flask context, until there's a better way, use this
VIEW_BOARD_URL = '/{}/'
VIEW_BOARD_URL_PAGE = '/{}/{}'
VIEW_THREAD_URL = '/{}/read/{}'
VIEW_CATALOG_URL = '/{}/catalog'


def purge_board(board: BoardModel):
    _purge(VIEW_BOARD_URL.format(board.name))
    for page in range(1, board.config.pages + 1):
        _purge(VIEW_BOARD_URL_PAGE.format(board.name, page))
    _purge(VIEW_CATALOG_URL.format(board.name))


def purge_thread(board: BoardModel, thread: ThreadModel) -> Future:
    return _purge(VIEW_THREAD_URL.format(board.name, thread.refno))


_pool = ThreadPoolExecutor(4)


def _purge(endpoint):
    if configuration.varnish.purging_enabled:
        url = configuration.varnish.server + endpoint

        return _pool.submit(_call_purge, url)


def _call_purge(url):
    host = urlparse(configuration.app.site_url).netloc

    try:
        res = requests.request(
            'PURGE',
            url,
            headers={
                'Host': host,
                'User-Agent': 'app'
            },
            timeout=1.0
        )
        res.raise_for_status()
    except RequestException:
        logger.error('Failed to purge "{}"'.format(url), exc_info=True)
