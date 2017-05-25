from sqlalchemy import Column, String, LargeBinary, ForeignKey, Integer, BigInteger, Boolean
from sqlalchemy.dialects.postgresql import ARRAY, JSON
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.orm import backref, relationship, deferred

from uchan.lib.database import OrmModelBase

"""
Models for SqlAlchemy.
"""


class MutableList(Mutable, list):
    def append(self, value):
        list.append(self, value)
        self.changed()

    def remove(self, value):
        list.remove(self, value)
        self.changed()

    @classmethod
    def coerce(cls, key, value):
        if not isinstance(value, MutableList):
            if isinstance(value, list):
                return MutableList(value)
            return Mutable.coerce(key, value)
        else:
            return value


def create_moderator_for_proxy(moderator):
    board_moderator = BoardModeratorOrmModel()
    board_moderator.moderator = moderator
    board_moderator.roles = []
    return board_moderator


class BoardOrmModel(OrmModelBase):
    __tablename__ = 'board'

    id = Column(Integer(), primary_key=True)
    name = Column(String(128), unique=True, index=True, nullable=False)
    refno_counter = Column(Integer(), nullable=False, default=1)
    config_id = Column(Integer, ForeignKey('config.id'), nullable=False, index=True)

    config = relationship('ConfigOrmModel', cascade='all')
    threads = relationship('ThreadOrmModel', backref='board', cascade='all, delete-orphan')
    logs = relationship('ModeratorLogOrmModel', backref='board')

    moderators = association_proxy('board_moderators', 'moderator', creator=create_moderator_for_proxy)


class BoardModeratorOrmModel(OrmModelBase):
    __tablename__ = 'boardmoderator'

    board_id = Column(Integer, ForeignKey('board.id'), primary_key=True)
    moderator_id = Column(Integer, ForeignKey('moderator.id'), primary_key=True)

    roles = Column(MutableList.as_mutable(ARRAY(String)), index=True, nullable=False)

    board = relationship(BoardOrmModel, backref=backref('board_moderators', cascade='all, delete-orphan'))
    moderator = relationship('ModeratorOrmModel', backref=backref('board_moderators', cascade='all, delete-orphan'))


class ConfigOrmModel(OrmModelBase):
    __tablename__ = 'config'

    id = Column(Integer(), primary_key=True)
    type = Column(String(), index=True)
    config = Column(JSON(), nullable=False, default='{}')


def create_board_for_proxy(board):
    board_moderator = BoardModeratorOrmModel()
    board_moderator.board = board
    board_moderator.roles = []
    return board_moderator


class ModeratorOrmModel(OrmModelBase):
    __tablename__ = 'moderator'

    id = Column(Integer(), primary_key=True)
    username = Column(String(), nullable=False, unique=True)
    password = deferred(Column(LargeBinary(), nullable=False))

    roles = Column(MutableList.as_mutable(ARRAY(String)), nullable=False, index=True)

    # Bans given by this moderator
    given_bans = relationship('BanOrmModel', backref='moderator')

    posts = relationship('PostOrmModel', backref='moderator')

    boards = association_proxy('board_moderators', 'board', creator=create_board_for_proxy)

    logs = relationship('ModeratorLogOrmModel', backref='moderator')


class PostOrmModel(OrmModelBase):
    __tablename__ = 'post'

    id = Column(Integer(), primary_key=True)

    thread_id = Column(Integer(), ForeignKey('thread.id'), nullable=False, index=True)
    # thread is a backref property

    moderator_id = Column(Integer(), ForeignKey('moderator.id'), nullable=True, index=True)
    # moderator is a backref property

    report = relationship('ReportOrmModel', backref='post', cascade='all, delete-orphan')

    file = relationship('FileOrmModel', backref='post', uselist=False, lazy='joined', cascade='all, delete-orphan')

    date = Column(BigInteger(), nullable=False, index=True)
    name = Column(String())
    subject = Column(String())
    text = Column(String(), index=True)
    refno = Column(Integer(), nullable=False, index=True)
    password = Column(String())
    ip4 = Column(BigInteger(), nullable=False, index=True)


class ReportOrmModel(OrmModelBase):
    __tablename__ = 'report'

    id = Column(Integer(), primary_key=True)
    post_id = Column(Integer(), ForeignKey('post.id'), nullable=False, index=True)
    # post is a backref property
    count = Column(Integer(), nullable=False)
    date = Column(BigInteger(), nullable=False, index=True)


class SessionOrmModel(OrmModelBase):
    __tablename__ = 'session'

    session_id = Column(String(32), primary_key=True)  # Length of a uuid4 with the - stripped
    data = Column(JSON(), nullable=False)
    expires = Column(BigInteger(), nullable=False, index=True)


class ThreadOrmModel(OrmModelBase):
    __tablename__ = 'thread'

    id = Column(Integer(), primary_key=True)

    board_id = Column(Integer(), ForeignKey('board.id'), nullable=False, index=True)
    # board is a backref property
    refno = Column(Integer(), nullable=False, index=True)

    last_modified = Column(BigInteger(), nullable=False, index=True)
    refno_counter = Column(Integer(), nullable=False, default=1)
    sticky = Column(Boolean(), nullable=False, default=False)
    locked = Column(Boolean(), nullable=False, default=False)

    posts = relationship('PostOrmModel', order_by='PostOrmModel.id', backref='thread', cascade='all, delete-orphan')


class FileOrmModel(OrmModelBase):
    __tablename__ = 'file'

    id = Column(Integer(), primary_key=True)
    location = Column(String(), nullable=False, index=True)
    thumbnail_location = Column(String(), nullable=False, index=True)
    post_id = Column(Integer(), ForeignKey('post.id'), nullable=False, index=True)
    # post is a backref property
    original_name = Column(String(), nullable=False)
    width = Column(Integer(), nullable=False)
    height = Column(Integer(), nullable=False)
    size = Column(Integer(), nullable=False)
    thumbnail_width = Column(Integer(), nullable=False)
    thumbnail_height = Column(Integer(), nullable=False)


class BanOrmModel(OrmModelBase):
    __tablename__ = 'ban'

    id = Column(Integer(), primary_key=True)
    ip4 = Column(BigInteger(), nullable=False, index=True)
    # Not null implies a range ban
    ip4_end = Column(BigInteger(), nullable=True, index=True)
    reason = Column(String(), nullable=False)
    date = Column(BigInteger(), nullable=False)
    # Use a length of 0 for permanent bans
    length = Column(BigInteger, nullable=False)
    board = Column(String(), nullable=True, index=True)

    post = Column(Integer(), ForeignKey('post.id'), nullable=True)

    # The moderator the ban was given by, or null when the moderator does not exist anymore
    moderator_id = Column(Integer(), ForeignKey('moderator.id'), nullable=True, index=True)
    # moderator is a backref property


class PageOrmModel(OrmModelBase):
    __tablename__ = 'page'

    id = Column(Integer(), primary_key=True)
    title = Column(String(), nullable=False, index=True)
    link_name = Column(String(), nullable=False, unique=True)
    type = Column(String(), nullable=False, index=True)
    order = Column(Integer(), nullable=False, index=True)
    content = Column(String(), nullable=False, index=True)


class VerificationOrmModel(OrmModelBase):
    __tablename__ = 'verification'

    verification_id = Column(String(32), primary_key=True)  # Length of a uuid4 with the - stripped
    ip4 = Column(BigInteger(), nullable=False, index=True)
    expires = Column(BigInteger(), nullable=False, index=True)
    data = Column(JSON(), nullable=False)


class ModeratorLogOrmModel(OrmModelBase):
    __tablename__ = 'moderatorlog'

    id = Column(Integer(), primary_key=True)
    date = Column(BigInteger(), nullable=False, index=True)
    moderator_id = Column(Integer(), ForeignKey('moderator.id'), nullable=True, index=True)
    # moderator is a backref property
    board_id = Column(Integer(), ForeignKey('board.id'), nullable=True, index=True)
    # board is a backref property

    type = Column(Integer(), nullable=False, index=True)
    text = Column(String(), nullable=False)
