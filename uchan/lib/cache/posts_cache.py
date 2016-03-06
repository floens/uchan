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

        # self.original_length = 0
        # self.omitted_count = 0


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
            thread_cache, thread_stub_cache = self.invalidate_thread_cache(thread_id)
        return thread_cache

    def find_thread_stub_cached(self, thread_id):
        key = self.get_thread_stub_cache_key(thread_id)
        thread_stub_cache = self.cache.get(key, True)
        if thread_stub_cache is None:
            thread_cache, thread_stub_cache = self.invalidate_thread_cache(thread_id)
        return thread_stub_cache

    def invalidate_thread_cache(self, thread_id):
        key = self.get_thread_cache_key(thread_id)
        stub_key = self.get_thread_stub_cache_key(thread_id)
        thread = g.posts_service.find_thread(thread_id, True)
        if not thread:
            self.cache.delete(key)
            self.cache.delete(stub_key)
            return None, None
        board_cache = BoardCacheProxy(thread.board).convert()
        thread_cache = ThreadCacheProxy(thread, board_cache, [PostCacheProxy(i).convert() for i in thread.posts]).convert()

        self.cache.set(key, thread_cache, timeout=0)

        op = thread_cache.posts[0]
        snippets = thread_cache.posts[1:][-PostsCache.BOARD_SNIPPET_COUNT:]

        thread_cache_stub = ThreadCacheProxy(thread, board_cache, [op] + snippets).convert()
        thread_cache_stub.original_length = len(thread_cache.posts)

        self.cache.set(stub_key, thread_cache_stub, timeout=0)

        return thread_cache, thread_cache_stub

    def get_thread_cache_key(self, thread_id):
        return 'thread${}'.format(thread_id)

    def get_thread_stub_cache_key(self, thread_id):
        return 'thread_stub${}'.format(thread_id)

    def find_board_cached(self, board_name, page=None):
        if page is None:
            key = self.get_board_cache_key(board_name)
            board_cache = self.cache.get(key, True)
            if board_cache is None:
                board_cache, board_pages_cache = self.invalidate_board_page_cache(board_name)
            return board_cache
        else:
            key = self.get_board_page_cache_key(board_name, page)
            board_page_cache = self.cache.get(key, True)
            if board_page_cache is None:
                board_cache, board_pages_cache = self.invalidate_board_page_cache(board_name)
                if board_pages_cache is None:
                    return None
                board_page_cache = board_pages_cache[page]
            return board_page_cache

    def invalidate_board_page_cache(self, board_name):
        board = g.board_service.find_board(board_name, True)
        if not board:
            self.cache.delete(self.get_board_cache_key(board_name))
            # Delete every page there could have been
            for i in range(15):
                self.cache.delete(self.get_board_page_cache_key(board_name, i))
            return None, None

        board_config = g.board_cache.find_board_config_cached(board_name)
        pages = board_config.board_config.pages
        threads_per_page = board_config.board_config.per_page

        # Collect the whole board
        # The non _op entries are for the board pages
        # the _op entries are for the catalog
        stickies_op = []
        stickies = []
        threads_op = []
        threads = []
        for thread in board.threads:
            thread_stub_cached = self.find_thread_stub_cached(thread.id)
            # The board and thread selects are done separately and there is thus the
            # possibility that the thread was removed after the board select
            if thread_stub_cached is None:
                continue

            thread_stub_cached.omitted_count = max(0, thread_stub_cached.original_length - 1 - 5)
            if thread_stub_cached.sticky:
                stickies.append(thread_stub_cached)
            else:
                threads.append(thread_stub_cached)

            thread_op_cached = CacheDict(thread_stub_cached)
            thread_op_cached.posts = [thread_op_cached.posts[0]]

            if thread_op_cached.sticky:
                stickies_op.append(thread_op_cached)
            else:
                threads_op.append(thread_op_cached)

        stickies_op = sorted(stickies_op, key=lambda t: t.last_modified, reverse=False)
        stickies = sorted(stickies, key=lambda t: t.last_modified, reverse=False)
        threads_op = sorted(threads_op, key=lambda t: t.last_modified, reverse=True)
        threads = sorted(threads, key=lambda t: t.last_modified, reverse=True)

        all_threads_op = stickies_op + threads_op
        all_threads = stickies + threads

        # All threads with just the op for the catalog
        board_cache_proxy = BoardCacheProxy(board)
        board_cache = BoardPageCacheProxy(board_cache_proxy, all_threads_op).convert()
        self.cache.set(self.get_board_cache_key(board_name), board_cache, timeout=0)

        # All threads with stubs, divided per page
        # note: there is the possibility that concurrent processes updating this cache
        # mess up the order / create duplicates of the page threads
        # this chance is however very low, and has no ill side effects except for
        # a visual glitch
        board_pages_cache = []
        for i in range(pages):
            from_index = i * threads_per_page
            to_index = (i + 1) * threads_per_page
            board_page_cache = BoardPageCacheProxy(board_cache_proxy, all_threads[from_index:to_index]).convert()
            self.cache.set(self.get_board_page_cache_key(board_name, i), board_page_cache, timeout=0)
            board_pages_cache.append(board_page_cache)

        return board_cache, board_pages_cache

    def get_board_cache_key(self, board_name):
        return 'board${}'.format(board_name)

    def get_board_page_cache_key(self, board_name, page):
        return 'board${}${}'.format(board_name, page)

    def invalidate_board(self, board_name):
        self.invalidate_board_page_cache(board_name)

    def delete_board_cache(self, board_name):
        threads = self.find_board_cached(board_name)
        for thread in threads.threads:
            self.cache.delete(self.get_thread_cache_key(thread.id))
            self.cache.delete(self.get_thread_stub_cache_key(thread.id))
        self.invalidate_board_page_cache(board_name)
