from uchan import g
from uchan.lib.cache import CacheDict, LocalCache
from uchan.lib.configs import BoardConfig


class AllBoardsCacheProxy(CacheDict):
    """Object to be memcached, contains a list of all boards, where each board is s BaordCacheProxy, containing only board info"""

    def __init__(self, boards):
        super().__init__()
        self.boards = boards


class BoardCacheProxy(CacheDict):
    def __init__(self, board):
        super().__init__()
        self.name = board.name
        self.id = board.id


class BoardCache:
    """
    Cache for all things board related.
    Anything related to posts (so the board pages and catalog) are in the PostsCache
    """

    def __init__(self, cache):
        self.cache = cache
        self.local_cache = LocalCache()

    def find_board_config(self, board_name):
        key = self.get_board_config_key(board_name)

        local_cached = self.local_cache.get(key)
        if local_cached is not None:
            return local_cached

        config_cache = self.cache.get(key, True)
        if config_cache is None:
            board = g.board_service.find_board(board_name)
            if not board:
                return None

            config_cache = g.config_service.load_config_dict(board.config)
            self.cache.set(key, config_cache)

        board_config = BoardConfig()
        board_config.set_values_from_cache(config_cache)

        self.local_cache.set(key, board_config)

        return board_config

    def get_board_config_key(self, board_name):
        return 'board_config${}'.format(board_name)

    def invalidate_board_config(self, board_name):
        self.cache.delete(self.get_board_config_key(board_name))

    def all_boards(self):
        key = 'all_boards'

        local_cached = self.local_cache.get(key)
        if local_cached is not None:
            return local_cached

        all_boards_cache = self.cache.get(key, True)
        if not all_boards_cache:
            all_boards = g.board_service.get_all_boards()
            all_boards_cache = AllBoardsCacheProxy([BoardCacheProxy(i).convert() for i in all_boards]).convert()
            self.cache.set(key, all_boards_cache, timeout=0)

        if all_boards_cache is not None:
            self.local_cache.set(key, all_boards_cache)

        return all_boards_cache

    def invalidate_all_boards(self):
        self.cache.delete('all_boards')
