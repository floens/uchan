from sqlalchemy.orm import lazyload
from sqlalchemy.orm.exc import NoResultFound

MAX_NAME_LENGTH = 35
MAX_SUBJECT_LENGTH = 100
MIN_PASSWORD_LENGTH = 5
MAX_PASSWORD_LENGTH = 25
MAX_TEXT_LENGTH = 2000
MAX_TEXT_LINES = 25

from uchan.lib import BadRequestError, ArgumentError, action_authorizer, plugin_manager
from uchan.lib.action_authorizer import PostAction, NoPermissionError, RequestBannedException
from uchan.lib.cache import board_cache, posts_cache, site_cache
from uchan.lib.crypt_code_compat import generate_crypt_code
from uchan.lib.database import get_db
from uchan.lib.mod_log import mod_log
from uchan.lib.models import Post, Report, Thread, File, Board
from uchan.lib.service import ban_service, board_service, moderator_service, report_service
from uchan.lib.tasks.post_task import ManagePostDetails
from uchan.lib.utils import now, ip4_to_str


def handle_post_check(post_details):
    board, thread = _get_board_thread(post_details)

    plugin_manager.execute_hook('on_handle_post_check', post_details)

    # Get moderator if mod_id was set
    moderator = None
    if post_details.mod_id is not None:
        moderator = moderator_service.find_moderator_id(post_details.mod_id)
        if moderator is None:
            raise Exception('Moderator not found')

    if thread is not None and thread.locked:
        raise ArgumentError('Thread is locked')

    action_authorizer.authorize_post_action(moderator, PostAction.POST_CREATE, post_details=post_details,
                                            board=board, thread=thread)

    board_config = board_cache.find_board_config(board.name)
    if post_details.has_file and not board_config.get('file_posting_enabled'):
        raise ArgumentError('File posting is disabled')

    if not post_details.text or not post_details.text.strip():
        # Allow no text when an image is attached
        if not post_details.has_file:
            raise ArgumentError('No text')

    if post_details.text is not None:
        if len(post_details.text) > MAX_TEXT_LENGTH:
            raise ArgumentError('Text too long')

        if len(post_details.text.splitlines()) > MAX_TEXT_LINES:
            raise ArgumentError('Too many lines')

    if post_details.name is not None and len(post_details.name) > MAX_NAME_LENGTH:
        raise ArgumentError('Name too long')

    if post_details.password is not None:
        if len(post_details.password) < MIN_PASSWORD_LENGTH:
            raise ArgumentError(
                'Password too short, at least {} characters required'.format(MIN_PASSWORD_LENGTH))

        if len(post_details.password) > MAX_PASSWORD_LENGTH:
            raise ArgumentError('Password too long, at most {} characters allowed'.format(MAX_PASSWORD_LENGTH))


def handle_post(post_details):
    start_time = now()

    board, to_thread = _get_board_thread(post_details)

    plugin_manager.execute_hook('on_handle_post', post_details)

    db = get_db()

    site_config = site_cache.find_site_config()
    default_name = site_config.get('default_name')
    board_config = board_cache.find_board_config(board.name)
    pages = board_config.get('pages')
    per_page = board_config.get('per_page')
    bump_limit = board_config.get('bump_limit')

    # Get moderator if mod_id was set
    moderator = None
    if post_details.mod_id is not None:
        moderator = moderator_service.find_moderator_id(post_details.mod_id)
        if moderator is None:
            raise Exception('Moderator not found')

    post = Post()
    post.date = now()
    post.ip4 = post_details.ip4

    if moderator is not None and moderator_service.moderates_board(moderator, board):
        post.moderator = moderator

    _handle_text(post, post_details)
    sage = _handle_name(post, post_details, default_name)
    _handle_subject(post, post_details, to_thread)
    _handle_password(post, post_details)

    db.add(post)

    if post_details.uploaded_file is not None:
        _attach_file(post, post_details.uploaded_file)

    if to_thread is None:
        return _make_thread(db, board, post, post_details, pages, per_page, start_time)
    else:
        return _make_post(db, board, post, to_thread, post_details, bump_limit, sage, start_time)


def _make_thread(db, board, post, post_details, pages, per_page, start_time):
    board_name = board.name

    thread = Thread()
    thread.last_modified = now()
    thread.refno = 0
    thread.board = board
    post.thread = thread
    post.refno = 1
    db.add(thread)

    # Atomically update the refno counter
    board.refno_counter = Board.refno_counter + 1
    db.commit()

    # Set it to the board after the commit to make sure there aren't any duplicates
    thread_refno = thread.refno = board.refno_counter

    # Purge overflowed threads
    threads_refnos_to_invalidate = _purge_threads(board, pages, per_page)
    db.commit()

    # Update caches and log it
    insert_time = now() - start_time
    start_time = now()

    for threads_refno_to_invalidate in threads_refnos_to_invalidate:
        posts_cache.invalidate_thread_cache(board_name, threads_refno_to_invalidate)
    posts_cache.invalidate_thread_cache(board_name, thread_refno)
    posts_cache.invalidate_board_page_cache(board_name)

    cache_time = now() - start_time
    log = 'new thread /{}/{} ({})'.format(board_name, thread_refno,
                                          _gather_statistics(insert_time, cache_time, post_details))
    mod_log(log, ip4_str=ip4_to_str(post_details.ip4))

    return board_name, thread_refno, 1


def _make_post(db, board, post, to_thread, post_details, bump_limit, sage, start_time):
    board_name = board.name
    thread_refno = to_thread.refno

    post.thread = to_thread
    post.refno = 0

    # Atomically update the refno counter
    to_thread.refno_counter = Thread.refno_counter + 1
    db.commit()

    # Set it to the post after the commit to make sure there aren't any duplicates
    post_refno = post.refno = to_thread.refno_counter
    post_id = post.id

    # Use the refno to avoid a count(*)
    if not sage and post_refno <= bump_limit:
        to_thread.last_modified = now()
    db.commit()

    # Update caches and log it
    insert_time = now() - start_time
    start_time = now()

    posts_cache.invalidate_thread_cache(board_name, thread_refno)
    posts_cache.invalidate_board_page_cache(board_name)

    cache_time = now() - start_time
    log = 'new reply /{}/{}#{} (id: {} {})'.format(
        board_name, thread_refno, post_refno, post_id,
        _gather_statistics(insert_time, cache_time, post_details))
    mod_log(log, ip4_str=ip4_to_str(post_details.ip4))

    return board_name, thread_refno, post_refno


def _handle_text(post, post_details):
    if post_details.text is not None:
        post.text = post_details.text.strip()
    else:
        post.text = ''


def _handle_password(post, post_details):
    if post_details.password is not None:
        post.password = post_details.password


def _handle_subject(post, post_details, to_thread):
    if to_thread is None and post_details.subject is not None:
        post.subject = post_details.subject


def _handle_name(post, post_details, default_name):
    sage = False
    post.name = default_name
    if post_details.name is not None:
        stripped_name = post_details.name.strip()
        if stripped_name:
            if '#' in post_details.name:
                raw_name, password = stripped_name.split('#', maxsplit=1)
                raw_name = raw_name.replace('!', '')
                if raw_name is not None and password:
                    # Styling is applied later
                    post.name = raw_name + ' !' + generate_crypt_code(password)
            elif stripped_name.lower() == 'sage':
                sage = True
                post.name = default_name
            else:
                name = stripped_name.replace('!', '')
                if name:
                    post.name = name
    return sage


def _gather_statistics(insert_time, cache_time, post_details):
    total = insert_time + cache_time + post_details.check_time
    file_time = ''
    if post_details.has_file:
        total += post_details.file_time
        file_time = 'file: {}ms, '.format(post_details.file_time)

    s = 'check: {}ms, {}db: {}ms, caches: {}ms, total: {}ms'
    return s.format(post_details.check_time, file_time, insert_time, cache_time, total)


def _get_board_thread(post_details):
    board = board_service.find_board(post_details.board_name)
    if not board:
        raise ArgumentError('Board not found')

    thread = None
    if post_details.thread_refno is not None:
        thread = find_thread_refno(post_details.board_name, post_details.thread_refno)
        if thread is None:
            raise ArgumentError('Thread not found')

    return board, thread


def _attach_file(post, uploaded_file):
    file = File()
    file.location = uploaded_file.location
    file.thumbnail_location = uploaded_file.thumbnail_location
    file.original_name = uploaded_file.original_name
    file.post = post
    file.width = uploaded_file.width
    file.height = uploaded_file.height
    file.size = uploaded_file.size
    file.thumbnail_width = uploaded_file.thumbnail_width
    file.thumbnail_height = uploaded_file.thumbnail_height
    db = get_db()
    db.add(file)


def handle_manage_post(details: ManagePostDetails):
    thread = find_thread_refno(details.board_name, details.thread_refno)
    if thread is None:
        raise BadRequestError('Thread not found')

    # Get moderator if mod_id was set
    moderator = None
    moderator_name = None
    if details.mod_id is not None:
        moderator = moderator_service.find_moderator_id(details.mod_id)
        if moderator is None:
            raise Exception('Moderator not found')
        else:
            moderator_name = moderator.username

    board = thread.board

    # You cannot manage when you are banned
    if ban_service.is_request_banned(details.ip4, board):
        raise RequestBannedException()

    if details.mode == ManagePostDetails.DELETE or details.mode == ManagePostDetails.REPORT:
        _manage_post(details, moderator, moderator_name)
    elif details.mode == ManagePostDetails.TOGGLE_STICKY or details.mode == ManagePostDetails.TOGGLE_LOCKED:
        _manage_thread(thread, board, details, moderator, moderator_name)
    else:
        raise Exception()


def _manage_post(details, moderator, moderator_name):
    post = find_post(details.post_id)
    if post is None:
        if not details.post_id:
            raise BadRequestError('No post selected')
        else:
            raise BadRequestError('Post not found')
    if details.mode == ManagePostDetails.DELETE:
        try:
            action_authorizer.authorize_post_action(moderator, PostAction.POST_DELETE, post, details)
            mod_log('post {} delete'.format(details.post_id), ip4_str=ip4_to_str(details.ip4),
                    moderator_name=moderator_name)
            delete_post(post)
        except NoPermissionError as e:
            mod_log('post {} delete failed, {}'.format(details.post_id, str(e)),
                    ip4_str=ip4_to_str(details.ip4), moderator_name=moderator_name)
            raise BadRequestError('Password invalid')
    elif details.mode == ManagePostDetails.REPORT:
        action_authorizer.authorize_post_action(moderator, PostAction.POST_REPORT, post, details)
        report = Report(post_id=post.id)
        mod_log('post {} reported'.format(post.id), ip4_str=ip4_to_str(details.ip4),
                moderator_name=moderator_name)
        report_service.add_report(report)


def _manage_thread(thread, board, details, moderator, moderator_name):
    if moderator is None:
        raise BadRequestError('Moderator not found')
    if details.mode == ManagePostDetails.TOGGLE_STICKY:
        action_authorizer.authorize_post_action(moderator, PostAction.THREAD_STICKY_TOGGLE, board=board)

        mod_log('sticky on /{}/{} {}'.format(
            thread.board.name, thread.id, 'disabled' if thread.sticky else 'enabled'),
            ip4_str=ip4_to_str(details.ip4), moderator_name=moderator_name)
        toggle_thread_sticky(thread)
    elif details.mode == ManagePostDetails.TOGGLE_LOCKED:
        action_authorizer.authorize_post_action(moderator, PostAction.THREAD_LOCKED_TOGGLE, board=board)

        mod_log('lock on /{}/{} {}'.format(
            thread.board.name, thread.id, 'disabled' if thread.locked else 'enabled'),
            ip4_str=ip4_to_str(details.ip4), moderator_name=moderator_name)
        toggle_thread_locked(thread)


def find_thread(thread_id, include_posts=False):
    try:
        q = get_db().query(Thread)
        if include_posts:
            q = q.options(lazyload('posts'))
        thread = q.filter_by(id=thread_id).one()

        if include_posts:
            # The thread and posts query are done separately
            # And thus there is a possibility that the second query returns empty data
            # when another transaction deletes the thread
            # Account for this by just returning None as if the thread didn't exist
            if not thread.posts:
                return None

        return thread
    except NoResultFound:
        return None


def find_thread_refno(board_name, thread_refno, include_posts=False):
    try:
        q = get_db().query(Thread)
        if include_posts:
            q = q.options(lazyload('posts'))
        thread = q.filter(Thread.refno == thread_refno,
                          Thread.board_id == Board.id,
                          Board.name == board_name).one()

        if include_posts:
            # See comment above
            if not thread.posts:
                return None

        return thread
    except NoResultFound:
        return None


def toggle_thread_sticky(thread):
    thread.sticky = not thread.sticky
    db = get_db()
    db.commit()

    # Invalidate caches
    posts_cache.invalidate_thread_cache(thread.board.name, thread.refno)
    posts_cache.invalidate_board_page_cache(thread.board.name)


def toggle_thread_locked(thread):
    thread.locked = not thread.locked
    db = get_db()
    db.commit()

    # Invalidate caches
    posts_cache.invalidate_thread_cache(thread.board.name, thread.refno)
    posts_cache.invalidate_board_page_cache(thread.board.name)


def find_post(post_id):
    try:
        return get_db().query(Post).filter_by(id=post_id).one()
    except NoResultFound:
        return None


def delete_file(post):
    if post.file is None:
        raise ArgumentError('No file on post')

    thread_refno = post.thread.refno
    board_name = post.thread.board.name
    db = get_db()
    # The file_service listens to deletes and will delete it from the cdn
    db.delete(post.file)
    db.commit()

    # Invalidate caches
    posts_cache.invalidate_thread_cache(board_name, thread_refno)
    posts_cache.invalidate_board_page_cache(board_name)


def delete_post(post):
    if post.refno == 1:
        delete_thread(post.thread)
    else:
        thread_refno = post.thread.refno
        board_name = post.thread.board.name
        db = get_db()
        db.delete(post)
        db.commit()

        # Invalidate caches
        posts_cache.invalidate_thread_cache(board_name, thread_refno)
        posts_cache.invalidate_board_page_cache(board_name)


def delete_thread(thread):
    thread_refno = thread.refno
    board_name = thread.board.name

    db = get_db()
    db.delete(thread)
    db.commit()

    # Invalidate caches
    posts_cache.invalidate_thread_cache(board_name, thread_refno)
    posts_cache.invalidate_board_page_cache(board_name)


def _purge_threads(board, pages, per_page):
    max = (per_page * pages) - 1

    db = get_db()

    threads_refnos_to_invalidate = []
    overflowed_threads = db.query(Thread).order_by(Thread.last_modified.desc()).filter_by(board_id=board.id)[max:]
    for overflowed_thread in overflowed_threads:
        thread_refno = overflowed_thread.refno
        db.delete(overflowed_thread)
        threads_refnos_to_invalidate.append(thread_refno)
    return threads_refnos_to_invalidate
