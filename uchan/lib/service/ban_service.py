from sqlalchemy import desc
from sqlalchemy.orm.exc import NoResultFound

from uchan.lib import ArgumentError
from uchan.lib.database import get_db
from uchan.lib.models import Ban, Post
from uchan.lib.proxy_request import get_request_ip4
from uchan.lib.utils import now


class BanService:
    """Takes care of bans and post cooldowns"""

    NEW_THREAD_COOLDOWN = 600 * 1000
    NEW_POST_COOLDOWN = 60 * 1000
    MAX_BAN_TIME = 24 * 31 * 60 * 60 * 1000
    MAX_REASON_LENGTH = 250

    def __init__(self):
        pass

    def is_request_banned(self, ip4, board=None):
        bans = self.find_bans(ip4)
        return len(bans) > 0

    def is_request_suspended(self, ip4, board, thread):
        timeout = self.NEW_THREAD_COOLDOWN if thread is None else self.NEW_POST_COOLDOWN
        from_time = now() - timeout

        posts = self.find_post_by_ip4(ip4, from_time, thread)
        if posts:
            most_recent = posts[0]
            time_left = (most_recent.date + timeout - now()) // 1000
            return True, time_left
        return False, 0

    def find_post_by_ip4(self, ip4, from_time, for_thread=None):
        db = get_db()
        query = db.query(Post).filter((Post.ip4 == ip4) & (Post.date >= from_time))
        if for_thread is not None:
            query = query.filter_by(thread_id=for_thread.id)
        else:
            query = query.filter_by(refno=1)
        query = query.order_by(desc(Post.date))
        posts = query.all()
        return posts

    def get_request_bans(self):
        ip4 = get_request_ip4()
        return self.find_bans(ip4)

    def find_bans(self, ip4):
        db = get_db()
        bans = db.query(Ban).filter((Ban.ip4 == ip4) | ((Ban.ip4 <= ip4) & (Ban.ip4_end >= ip4))).all()
        applied_bans = []
        for ban in bans:
            if not self.ban_valid(ban):
                self.delete_ban(ban)
            elif self.ban_applies(ban, ip4):
                applied_bans.append(ban)
        return applied_bans

    def ban_applies(self, ban, ip4):
        if ban.ip4_end is not None:
            return ban.ip4 < ip4 < ban.ip4_end
        else:
            return ban.ip4 == ip4

    def ban_valid(self, ban):
        if ban.length == 0:
            return True
        return now() <= ban.date + ban.length

    def add_ban(self, ban):
        if ban.length > self.MAX_BAN_TIME:
            raise ArgumentError('Ban too long')

        if ban.ip4_end is not None:
            if ban.ip4_end <= ban.ip4:
                raise ArgumentError('ip4 end must be bigger than ip4')

        if ban.reason and len(ban.reason) > self.MAX_REASON_LENGTH:
            raise ArgumentError('Ban reason text too long')

        ban.date = now()

        db = get_db()
        db.add(ban)
        db.commit()

    def delete_ban(self, ban):
        db = get_db()
        db.delete(ban)
        db.commit()

    def find_ban_id(self, id):
        db = get_db()
        try:
            return db.query(Ban).filter_by(id=id).one()
        except NoResultFound:
            return None

    def get_all_bans(self):
        db = get_db()
        return db.query(Ban).all()
