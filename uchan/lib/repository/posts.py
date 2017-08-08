from typing import Optional, Tuple, List

from sqlalchemy import desc
from sqlalchemy.orm import Session, lazyload

from uchan.lib import document_cache
from uchan.lib.cache import cache, cache_key
from uchan.lib.database import session
from uchan.lib.exceptions import ArgumentError
from uchan.lib.model import PostModel, PostResultModel, BoardModel, ThreadModel, ThreadStubModel, \
    BoardPageModel, CatalogModel
from uchan.lib.ormmodel import ThreadOrmModel, BoardOrmModel, PostOrmModel, FileOrmModel
from uchan.lib.utils import now

MESSAGE_POST_HAS_NO_FILE = 'Post has no file'


def create_post(board: BoardModel, thread: ThreadModel, post: PostModel, sage: bool) \
        -> Tuple[PostResultModel, int, int]:
    start_time = now()
    with session() as s:
        post_orm_model = post.to_orm_model()

        s.add(post_orm_model)

        to_thread_orm_model = s.query(ThreadOrmModel).filter_by(id=thread.id).one()

        post_orm_model.thread = to_thread_orm_model
        post_orm_model.refno = 0

        # Atomically update the refno counter
        to_thread_orm_model.refno_counter = ThreadOrmModel.refno_counter + 1
        s.commit()

        # Set it to the post after the commit to make sure there aren't any duplicates
        post_refno = post_orm_model.refno = to_thread_orm_model.refno_counter
        post_id = post_orm_model.id

        # Attach file to the post id
        if post.file:
            file_orm_model = post.file.to_orm_model()
            file_orm_model.post_id = post_id
            s.add(file_orm_model)

        if post.moderator:
            post_orm_model.moderator_id = post.moderator.id

        modify_date = now()

        # Use the refno to avoid a count(*)
        if not sage and post_refno <= board.config.bump_limit:
            to_thread_orm_model.last_modified = modify_date
        s.commit()

        insert_time = now() - start_time
        start_time = now()

        _invalidate_thread_cache(s, thread, board)
        _invalidate_board_pages_catalog_cache(s, board)

        purge_thread_future = document_cache.purge_thread(board, thread)
        # Wait for the thread to be purged, otherwise the chance exists that the client reloads a cached version.
        # This only holds up the posting client, others have the updated memcache available.
        if purge_thread_future: purge_thread_future.result()
        # Don't wait for this
        document_cache.purge_board(board)

        cache_time = now() - start_time

        res = PostResultModel.from_board_name_thread_refno_post_refno(board.name, thread.refno, post_refno)
        return res, insert_time, cache_time


def create_thread(board: BoardModel, post: PostModel) \
        -> Tuple[PostResultModel, int, int]:
    start_time = now()
    with session() as s:
        board_orm_model = s.query(BoardOrmModel).filter_by(id=board.id).one()

        thread_orm_model = ThreadOrmModel()
        thread_orm_model.last_modified = now()
        thread_orm_model.refno = 0
        thread_orm_model.board_id = board.id

        post_orm_model = post.to_orm_model()

        post_orm_model.thread = thread_orm_model
        post_orm_model.refno = 1
        s.add(thread_orm_model)

        # Atomically update the refno counter
        board_orm_model.refno_counter = BoardOrmModel.refno_counter + 1
        s.commit()

        # Set it to the board after the commit to make sure there aren't any duplicates
        thread_refno = thread_orm_model.refno = board_orm_model.refno_counter

        # Attach file to the post id
        if post.file:
            file_orm_model = post.file.to_orm_model()
            file_orm_model.post_id = post_orm_model.id
            s.add(file_orm_model)

        if post.moderator:
            post_orm_model.moderator_id = post.moderator.id

        # Purge overflowed threads
        threads_refnos_to_purge = _purge_threads(s, board, board.config.pages, board.config.per_page)
        s.commit()

        insert_time = now() - start_time
        start_time = now()

        for purging_refno in threads_refnos_to_purge:
            cache.delete(cache_key('thread', board.name, purging_refno))
            cache.delete(cache_key('thread_stub', board.name, purging_refno))

        thread = ThreadModel.from_orm_model(thread_orm_model)
        _invalidate_thread_cache(s, thread, board)
        _invalidate_board_pages_catalog_cache(s, board)

        document_cache.purge_board(board)

        cache_time = now() - start_time

        res = PostResultModel.from_board_name_thread_refno_post_refno(board.name, thread_refno, 1)
        return res, insert_time, cache_time


def delete_post(post: PostModel):
    if post.refno == 1:
        delete_thread(post.thread)
    else:
        with session() as s:
            post_orm_model = s.query(PostOrmModel).filter_by(id=post.id).one()
            s.delete(post_orm_model)
            s.commit()

            thread = post.thread

            _invalidate_thread_cache(s, thread, thread.board)
            _invalidate_board_pages_catalog_cache(s, thread.board)

            document_cache.purge_thread(thread.board, thread)
            document_cache.purge_board(thread.board)


def delete_post_file(post: PostModel):
    if post.file is None:
        raise ArgumentError(MESSAGE_POST_HAS_NO_FILE)

    with session() as s:
        file_orm_model = s.query(FileOrmModel).filter_by(id=post.file.id).one()
        s.delete(file_orm_model)
        s.commit()

        thread = post.thread

        _invalidate_thread_cache(s, thread, thread.board)
        _invalidate_board_pages_catalog_cache(s, thread.board)

        document_cache.purge_thread(thread.board, thread)
        document_cache.purge_board(thread.board)


def delete_thread(thread: ThreadModel):
    with session() as s:
        thread_orm_model = s.query(ThreadOrmModel).filter_by(id=thread.id).one()
        s.delete(thread_orm_model)
        s.commit()

        _invalidate_thread_cache(s, thread, thread.board)
        _invalidate_board_pages_catalog_cache(s, thread.board)

        document_cache.purge_thread(thread.board, thread)
        document_cache.purge_board(thread.board)


def update_thread_sticky(thread: ThreadModel, sticky: bool):
    with session() as s:
        existing = s.query(ThreadOrmModel).filter_by(id=thread.id).one()
        existing.sticky = sticky
        s.commit()

        _invalidate_thread_cache(s, thread, thread.board)
        _invalidate_board_pages_catalog_cache(s, thread.board)

        document_cache.purge_thread(thread.board, thread)
        document_cache.purge_board(thread.board)


def update_thread_locked(thread: ThreadModel, locked: bool):
    with session() as s:
        existing = s.query(ThreadOrmModel).filter_by(id=thread.id).one()
        existing.locked = locked
        s.commit()

        _invalidate_thread_cache(s, thread, thread.board)
        _invalidate_board_pages_catalog_cache(s, thread.board)

        document_cache.purge_thread(thread.board, thread)
        document_cache.purge_board(thread.board)


def find_post_by_id(post_id: int, include_thread=False) -> Optional[PostModel]:
    with session() as s:
        m = s.query(PostOrmModel).filter_by(id=post_id).one_or_none()
        res = None
        if m:
            res = PostModel.from_orm_model(m, include_thread=include_thread)
        return res


# TODO: merge these two
def find_thread_by_board_name_thread_refno(board_name: str, thread_refno: int) -> Optional[ThreadModel]:
    thread_cache = cache.get(cache_key('thread', board_name, thread_refno))
    if not thread_cache:
        with session() as s:
            q = s.query(ThreadOrmModel)
            q = q.filter(ThreadOrmModel.refno == thread_refno,
                         ThreadOrmModel.board_id == BoardOrmModel.id,
                         BoardOrmModel.name == board_name)
            thread_orm_model = q.one_or_none()

            if not thread_orm_model:
                return None

            # TODO: also load board in q above
            thread = ThreadModel.from_orm_model(thread_orm_model, include_board=True)
            return thread

    if thread_cache:
        return ThreadModel.from_cache(thread_cache)
    return None


def find_thread_by_board_thread_refno_with_posts(board: BoardModel, thread_refno: int) -> Optional[ThreadModel]:
    thread_cache = cache.get(cache_key('thread', board.name, thread_refno))
    if not thread_cache:
        with session() as s:
            q = s.query(ThreadOrmModel)
            q = q.options(lazyload('posts'))
            q = q.filter(ThreadOrmModel.refno == thread_refno,
                         ThreadOrmModel.board_id == BoardOrmModel.id,
                         BoardOrmModel.name == board.name)
            thread_orm_model = q.one_or_none()

            if not thread_orm_model or not thread_orm_model.posts:
                return None

            # TODO: also load board in q above
            thread = ThreadModel.from_orm_model(thread_orm_model, include_board=True, include_posts=True)
            thread_cache = thread.to_cache(include_board=True, include_posts=True)
            cache.set(cache_key('thread', thread.board.name, thread.refno), thread_cache, timeout=0)
            return thread

    if thread_cache:
        return ThreadModel.from_cache(thread_cache)
    return None


def find_posts_by_ip4_from_time(ip4: int, from_time: int, by_thread: ThreadModel = None) -> List[PostModel]:
    with session() as s:
        q = s.query(PostOrmModel)
        q = q.filter((PostOrmModel.ip4 == ip4) & (PostOrmModel.date >= from_time))

        if by_thread:
            q = q.filter_by(thread_id=by_thread.id)
        else:
            q = q.filter_by(refno=1)

        q = q.order_by(desc(PostOrmModel.date))

        res = list(map(lambda i: PostModel.from_orm_model(i), q.all()))
        s.commit()
        return res


def get_board_page(board: BoardModel, page: int) -> BoardPageModel:
    board_page_cache = cache.get(cache_key('board', board.name, page))
    if not board_page_cache:
        with session() as s:
            catalog, board_pages = _invalidate_board_pages_catalog_cache(s, board)
            return board_pages[page]

    return BoardPageModel.from_cache(board_page_cache)


def get_catalog(board: BoardModel) -> CatalogModel:
    catalog_cache = cache.get(cache_key('board', board.name))
    if not catalog_cache:
        with session() as s:
            catalog, board_pages = _invalidate_board_pages_catalog_cache(s, board)
            return catalog

    return CatalogModel.from_cache(catalog_cache)


def _purge_threads(s: Session, board: BoardModel, pages: int, per_page: int):
    limit = (per_page * pages) - 1

    threads_refnos_to_invalidate = []

    q = s.query(ThreadOrmModel)
    q = q.order_by(ThreadOrmModel.last_modified.desc())
    q = q.filter_by(board_id=board.id)

    overflowed_threads = q[limit:]
    for overflowed_thread in overflowed_threads:
        thread_refno = overflowed_thread.refno
        s.delete(overflowed_thread)
        threads_refnos_to_invalidate.append(thread_refno)
    return threads_refnos_to_invalidate


def _gather_statistics(insert_time, cache_time, post_details):
    total = insert_time + cache_time
    file_time = ''
    if post_details.has_file:
        total += post_details.file_time
        file_time = 'file: {}ms, '.format(post_details.file_time)

    s = '{}db: {}ms, caches: {}ms, total: {}ms'
    return s.format(file_time, insert_time, cache_time, total)


BOARD_SNIPPET_COUNT = 5
BOARD_SNIPPET_MAX_LINES = 12


def _invalidate_thread_cache(s: Session, old_thread: ThreadModel, board: BoardModel):
    """
    Update the memcache version of the specified thread. This will update the thread cache,
    and the thread stub cache.
    """
    key = cache_key('thread', board.name, old_thread.refno)
    stub_key = cache_key('thread_stub', board.name, old_thread.refno)

    # Reuse the parsed html from the old cache.
    old_thread_posts_cache = cache.get(key)
    old_thread_posts = None
    if old_thread_posts_cache:
        old_thread_posts = ThreadModel.from_cache(old_thread_posts_cache).posts

    # Next, query all the new posts
    q = s.query(ThreadOrmModel)
    q = q.filter_by(id=old_thread.id)
    q = q.options(lazyload('posts'))
    res = q.one_or_none()
    if not res:
        cache.delete(key)
        cache.delete(stub_key)
        return

    thread = ThreadModel.from_orm_model(res, include_board=True, include_posts=True,
                                        cached_thread_posts=old_thread_posts)

    thread_cache = thread.to_cache(include_board=True, include_posts=True)
    cache.set(key, thread_cache, timeout=0)

    thread_stub = ThreadStubModel.from_thread(thread, include_snippets=True)
    thread_stub_cache = thread_stub.to_cache()
    cache.set(stub_key, thread_stub_cache, timeout=0)

    return thread, thread_stub


def _invalidate_board_pages_catalog_cache(s: Session, board: BoardModel):
    """
    Update the memcache version of the specified board.
    This will update the board pages from the already cached thread stubs, and create a new catalog cache.
    """

    q = s.query(ThreadOrmModel)
    q = q.filter(ThreadOrmModel.board_id == board.id)
    threads_orm = q.all()
    thread_models = list(map(lambda j: ThreadModel.from_orm_model(j, ), threads_orm))

    # This builds the board index, stickies first, oldest first, then normal posts, newest first.
    # The pages are split accordingly to the board config,
    # and the catalog is build from only the ops.
    stickies = []
    threads = []
    for thread in thread_models:
        thread_stub_cache = cache.get(cache_key('thread_stub', board.name, thread.refno))
        if not thread_stub_cache:
            thread, thread_stub = _invalidate_thread_cache(s, thread, board)
            # The board and thread selects are done separately and there is thus the
            # possibility that the thread was removed after the board select
            if thread_stub is None:
                continue
        else:
            thread_stub = ThreadStubModel.from_cache(thread_stub_cache)

        stickies.append(thread_stub) if thread_stub.sticky else threads.append(thread_stub)

    stickies = sorted(stickies, key=lambda t: t.last_modified, reverse=False)
    threads = sorted(threads, key=lambda t: t.last_modified, reverse=True)
    all_thread_stubs = stickies + threads

    # The catalog is a CatalogModel with ThreadStubs with only OP's
    catalog = CatalogModel.from_board_thread_stubs(board, all_thread_stubs)
    catalog_cache = catalog.to_cache()
    cache.set(cache_key('board', board.name), catalog_cache, timeout=0)

    # All threads with stubs, divided per page
    # note: there is the possibility that concurrent processes updating this cache
    # mess up the order / create duplicates of the page threads
    # this chance is however very low, and has no ill side effects except for
    # a visual glitch
    board_pages = []
    for i in range(board.config.pages):
        from_index = i * board.config.per_page
        to_index = (i + 1) * board.config.per_page

        board_page = BoardPageModel.from_page_thread_stubs(i, all_thread_stubs[from_index:to_index])
        board_pages.append(board_page)

        board_page_cache = board_page.to_cache()
        cache.set(cache_key('board', board.name, i), board_page_cache, timeout=0)

    return catalog, board_pages
