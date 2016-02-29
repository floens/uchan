from uchan import g
from uchan.filter.text_parser import parse_text
from uchan.lib import roles

from uchan.lib.cache import CacheDict


# Object to be memcached, containing only board info
class BoardCacheProxy(CacheDict):
    def __init__(self, board):
        super().__init__(self)
        self.name = board.name


# Object to be memcached, containing threads with their last n replies
class BoardPageCacheProxy(CacheDict):
    def __init__(self, board, threads):
        super().__init__()
        self.board = board
        self.threads = threads


# Object to be memcached, contains all posts with a PostCacheProxy
class ThreadCacheProxy(CacheDict):
    def __init__(self, thread, board, posts):
        super().__init__()
        self.id = thread.id
        self.last_modified = thread.last_modified
        self.locked = thread.locked
        self.sticky = thread.sticky
        self.board = board
        self.posts = posts


# Object to be memcached, containing post info
class PostCacheProxy(CacheDict):
    def __init__(self, post):
        super().__init__()
        self.id = post.id
        self.date = post.date
        self.name = post.name
        self.subject = post.subject
        self.text = post.text
        self.html = parse_text(post.text)
        self.refno = post.refno

        self.mod_code = None
        if post.moderator is not None:
            moderator = post.moderator
            self.mod_code = '## ' + roles.get_role_name(moderator.roles)
            if post.with_mod_name:
                self.mod_code = moderator.username + ' ' + self.mod_code

        self.has_file = post.file is not None
        if self.has_file:
            self.file_location = g.file_service.resolve_to_uri(post.file.location)
            self.file_thumbnail_location = g.file_service.resolve_to_uri(post.file.thumbnail_location)
            self.file_name = post.file.original_name
            self.file_width = post.file.width
            self.file_height = post.file.height
            self.file_size = post.file.size
            self.file_thumbnail_width = post.file.thumbnail_width
            self.file_thumbnail_height = post.file.thumbnail_height


class PostsCache:
    BOARD_SNIPPET_COUNT = 5

    def __init__(self, cache):
        self.cache = cache

    def find_thread_cached(self, thread_id):
        key = self.get_thread_cache_key(thread_id)
        thread_cache = self.cache.get(key, True)
        if thread_cache is None:
            thread = g.posts_service.find_thread(thread_id, True)
            if not thread:
                return None
            thread_cache = ThreadCacheProxy(thread, BoardCacheProxy(thread.board).convert(),
                                            [PostCacheProxy(i).convert() for i in thread.posts]).convert()
            self.cache.set(key, thread_cache, timeout=0)
        return thread_cache

    def invalidate_thread_cache(self, thread_id):
        key = self.get_thread_cache_key(thread_id)
        self.cache.delete(key)

    def get_thread_cache_key(self, thread_id):
        key = 'thread_{}'.format(thread_id)
        return key

    def find_board_cached(self, board_name, page=None):
        key = self.get_board_page_cache_key(board_name)
        board_cache = self.cache.get(key, True)
        if board_cache is None:
            board = g.board_service.find_board(board_name, True)
            if not board:
                return None

            stickies = []
            threads = []
            for thread in board.threads:
                thread_cached = self.find_thread_cached(thread.id)
                original_length = len(thread_cached.posts)

                op = thread_cached.posts[0]
                snippets = thread_cached.posts[-PostsCache.BOARD_SNIPPET_COUNT:]
                if snippets and snippets[0].id == op.id:
                    snippets = snippets[1:]

                thread_cached.posts = [op] + snippets
                thread_cached.omitted_count = original_length - 1 - 5
                if thread_cached.sticky:
                    stickies.append(thread_cached)
                else:
                    threads.append(thread_cached)

            stickies = sorted(stickies, key=lambda t: t.last_modified, reverse=False)
            threads = sorted(threads, key=lambda t: t.last_modified, reverse=True)

            board_cache = BoardPageCacheProxy(BoardCacheProxy(board), stickies + threads).convert()
            self.cache.set(key, board_cache, timeout=0)

        if page is None:
            return BoardPageCacheProxy(board_cache.board, board_cache.threads).convert()
        else:
            board_config = g.board_cache.find_board_config_cached(board_name)
            per_page = board_config.board_config.per_page
            from_index = page * per_page
            to_index = (page + 1) * per_page
            return BoardPageCacheProxy(board_cache.board, board_cache.threads[from_index:to_index]).convert()

    def invalidate_board_page_cache(self, board_name):
        key = self.get_board_page_cache_key(board_name)
        self.cache.delete(key)

    def get_board_page_cache_key(self, board_name):
        key = 'board_{}'.format(board_name)
        return key

    def invalidate_board(self, board_name):
        self.invalidate_board_page_cache(board_name)
