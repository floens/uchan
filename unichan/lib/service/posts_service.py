import time

from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound

import config
from unichan import g
from unichan.database import get_db
from unichan.filter.post_parser import validate_post, parse_post
from unichan.lib import BadRequestError, ArgumentError
from unichan.lib.models import Post, Report, Thread
from unichan.lib.tasks.post_task import ManagePostDetails


def now():
    return int(time.time() * 1000)


class PostsService:
    def handle_post(self, post_details):
        db = get_db()
        new_thread = post_details.thread_id is None

        board = g.board_service.find_board(post_details.board_name)
        if not board:
            raise BadRequestError('Board not found')
        board_name = board.name

        site_config_cached = g.site_cache.find_site_config_cached()

        sage = False
        try:
            if not post_details.name:
                post_details.name = site_config_cached.default_name

            validate_post(post_details.text)
            parse_post(post_details.text)

            post = Post()
            post.text = post_details.text

            post.name = post_details.name
            if post.name.lower() == 'sage':
                sage = True

            if new_thread:
                post.subject = post_details.subject
            post.password = post_details.password
            post.date = now()
        except ArgumentError as e:
            raise BadRequestError(e.message)

        db.add(post)

        if new_thread:
            post.refno = 1

            thread = Thread()
            thread.last_modified = now()
            thread.posts.append(post)
            board.threads.append(thread)
            db.add(thread)

            g.posts_cache.invalidate_board_page_cache(board.name)
            g.posts_cache.invalidate_thread_cache(thread.id)
            self.on_post_created(post, board)
            db.commit()

            return board_name, thread.id
        else:
            thread_id = post_details.thread_id
            thread = self.find_thread(thread_id)
            if thread is None:
                raise BadRequestError('Thread not found')

            thread.refno_counter += 1

            thread_len = db.query(Post).filter_by(thread_id=thread_id).count()

            board_config = g.config_service.load_config(board.config)

            if not sage or thread_len < board_config.get('bump_limit'):
                thread.last_modified = now()

            post.refno = thread.refno_counter
            thread.posts.append(post)
            self.on_post_created(post, board)
            db.commit()
            g.posts_cache.invalidate_board_page_cache(board_name)
            g.posts_cache.invalidate_thread_cache(thread_id)

            return board_name, thread_id

    def handle_manage_post(self, details):
        post = self.find_post(details.post_id)
        if not post:
            raise BadRequestError('Post not found')

        if details.mode == ManagePostDetails.DELETE:
            moderator = None
            if details.mod_id is not None:
                moderator = g.moderator_service.find_moderator_id(details.mod_id)
                if moderator is None:
                    raise Exception('Moderator not found')

            moderator_can_delete = moderator is not None and g.moderator_service.moderates_board(moderator,
                                                                                                 post.thread.board)
            can_delete = moderator_can_delete or (details.password is not None and details.password == post.password)
            if can_delete:
                self.delete_post(post)
            else:
                raise BadRequestError('Password invalid')
        elif details.mode == ManagePostDetails.REPORT:
            report = Report(post_id=post.id)
            self.add_report(report)
        else:
            raise Exception()

    def find_thread(self, thread_id, include_posts=False):
        try:
            q = get_db().query(Thread)
            if include_posts:
                q = q.options(joinedload('posts'))
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
            self.on_post_deleted(post)
            db.delete(post)
            db.commit()

    def delete_thread(self, thread):
        # Invalidate caches
        g.posts_cache.invalidate_board_page_cache(thread.board.name)
        g.posts_cache.invalidate_thread_cache(thread.id)

        db = get_db()
        for post in thread.posts:
            self.on_post_deleted(post)
        db.delete(thread)
        db.commit()

    def on_post_created(self, post, board=None):
        per_page = 4
        pages = 2
        max = per_page * pages

        if board is None:
            board = post.thread.board

        db = get_db()

        overflowed_threads = db.query(Thread).order_by(Thread.last_modified.desc()).filter_by(board_id=board.id)[max:]
        for overflowed_thread in overflowed_threads:
            self.delete_thread(overflowed_thread)

    def on_post_deleted(self, post):
        print('post {} deleted'.format(post.id))

    def add_report(self, report):
        db = get_db()

        exiting_report = None
        try:
            exiting_report = db.query(Report).filter_by(post_id=report.post_id).one()
        except NoResultFound:
            pass

        if exiting_report is not None:
            exiting_report.count += 1
        else:
            report.count = 1
            db.add(report)

        db.commit()
