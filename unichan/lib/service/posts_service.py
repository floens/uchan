from sqlalchemy.orm import lazyload
from sqlalchemy.orm.exc import NoResultFound

import config
from unichan import g
from unichan.database import get_db
from unichan.lib import roles
from unichan.lib import BadRequestError, ArgumentError
from unichan.lib.models import Post, Report, Thread, File
from unichan.lib.tasks.post_task import ManagePostDetails
from unichan.lib.utils import now


class RequestBannedException(ArgumentError):
    def __init__(self, *args):
        ArgumentError.__init__(self, *args)


class RequestSuspendedException(ArgumentError):
    def __init__(self, *args):
        ArgumentError.__init__(self, *args)


class PostsService:
    MAX_NAME_LENGTH = 35
    MAX_SUBJECT_LENGTH = 100
    MAX_PASSWORD_LENGTH = 25
    MAX_TEXT_LENGTH = 2000
    MAX_TEXT_LINES = 25

    def handle_post_check(self, post_details):
        board, thread = self.get_board_thread(post_details)

        if g.ban_service.is_request_banned(post_details.ip4, board):
            raise RequestBannedException()

        if config.ENABLE_COOLDOWN_CHECKING and g.ban_service.is_request_suspended(post_details.ip4, board, thread):
            raise RequestSuspendedException()

        if not post_details.text.strip():
            # Allow no text when an image is attached
            if not post_details.has_file:
                raise ArgumentError('No text')

        if len(post_details.text) > self.MAX_TEXT_LENGTH:
            raise ArgumentError('Text too long')

        if len(post_details.text.splitlines()) > self.MAX_TEXT_LINES:
            raise ArgumentError('Too many lines')

        if post_details.name and len(post_details.name) > self.MAX_NAME_LENGTH:
            raise ArgumentError('Name too long')

        if post_details.password and len(post_details.password) > self.MAX_PASSWORD_LENGTH:
            raise ArgumentError('Password too long')

    def handle_post(self, post_details):
        board, to_thread = self.get_board_thread(post_details)

        db = get_db()

        site_config_cached = g.site_cache.find_site_config_cached()
        board_config_cached = g.board_cache.find_board_config_cached(board.name)

        post = Post()
        post.text = post_details.text.strip()
        if post_details.name:
            post.name = post_details.name
        else:
            post.name = site_config_cached.default_name
        sage = post.name.lower() == 'sage'
        if to_thread is None and post_details.subject:
            post.subject = post_details.subject
        if post_details.password:
            post.password = post_details.password
        post.date = now()
        post.ip4 = post_details.ip4

        db.add(post)

        if post_details.uploaded_file is not None:
            self.attach_file(post, post_details.uploaded_file)

        if to_thread is None:
            board_name = board.name

            post.refno = 1

            thread = Thread()
            thread.last_modified = now()
            thread.posts.append(post)
            board.threads.append(thread)
            db.add(thread)

            self.on_post_created(post, board, board_config_cached)
            db.commit()
            g.posts_cache.invalidate_board_page_cache(board.name)
            g.posts_cache.invalidate_thread_cache(thread.id)

            return board_name, thread.id, 1
        else:
            board_name = board.name
            thread_id = to_thread.id

            to_thread.refno_counter += 1

            thread_len = db.query(Post).filter_by(thread_id=thread_id).count()

            if not sage and thread_len < board_config_cached.board_config.bump_limit:
                to_thread.last_modified = now()

            post_refno = post.refno = to_thread.refno_counter
            to_thread.posts.append(post)

            self.on_post_created(post, board, board_config_cached)
            db.commit()
            g.posts_cache.invalidate_board_page_cache(board_name)
            g.posts_cache.invalidate_thread_cache(thread_id)

            return board_name, thread_id, post_refno

    def get_board_thread(self, post_details):
        board = g.board_service.find_board(post_details.board_name)
        if not board:
            raise ArgumentError('Board not found')

        thread = None
        if post_details.thread_id is not None:
            thread = g.posts_service.find_thread(post_details.thread_id)
            if thread is None:
                raise ArgumentError('Thread not found')

        return board, thread

    def attach_file(self, post, uploaded_file):
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

    def handle_manage_post(self, details):
        post = self.find_post(details.post_id)
        if not post:
            raise BadRequestError('Post not found')

        board = post.thread.board

        moderator = None
        if details.mod_id is not None:
            moderator = g.moderator_service.find_moderator_id(details.mod_id)
            if moderator is None:
                raise Exception('Moderator not found')

        if moderator is None or not g.moderator_service.has_role(moderator, roles.ROLE_ADMIN):
            if g.ban_service.is_request_banned(details.ip4, board):
                raise RequestBannedException()

        if details.mode == ManagePostDetails.DELETE:
            can_delete = (moderator is not None and g.moderator_service.can_delete(moderator, post)) or \
                         (details.password is not None and details.password == post.password)
            if can_delete:
                self.delete_post(post)
            else:
                raise BadRequestError('Password invalid')
        elif details.mode == ManagePostDetails.REPORT:
            report = Report(post_id=post.id)
            g.moderator_service.add_report(report)
        else:
            raise Exception()

    def find_thread(self, thread_id, include_posts=False):
        try:
            q = get_db().query(Thread)
            if include_posts:
                q = q.options(lazyload('posts'))
            thread = q.filter_by(id=thread_id).one()
            return thread
        except NoResultFound:
            return None

    def find_post(self, post_id):
        try:
            return get_db().query(Post).filter_by(id=post_id).one()
        except NoResultFound:
            return None

    def delete_post(self, post):
        if post.refno == 1:
            self.delete_thread(post.thread)
        else:
            # Invalidate caches
            g.posts_cache.invalidate_board_page_cache(post.thread.board.name)
            g.posts_cache.invalidate_thread_cache(post.thread.id)

            db = get_db()
            db.delete(post)
            db.commit()

    def delete_thread(self, thread):
        # Invalidate caches
        g.posts_cache.invalidate_board_page_cache(thread.board.name)
        g.posts_cache.invalidate_thread_cache(thread.id)

        db = get_db()
        db.delete(thread)
        db.commit()

    def on_post_created(self, post, board, board_config_cached):
        pages = board_config_cached.board_config.pages
        per_page = board_config_cached.board_config.per_page
        max = per_page * pages

        db = get_db()

        overflowed_threads = db.query(Thread).order_by(Thread.last_modified.desc()).filter_by(board_id=board.id)[max:]
        for overflowed_thread in overflowed_threads:
            self.delete_thread(overflowed_thread)
