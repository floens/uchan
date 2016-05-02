from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship, backref

from uchan.lib.database import ModelBase
from uchan.lib.models import MutableList


def create_moderator_for_proxy(moderator):
    board_moderator = BoardModerator()
    board_moderator.moderator = moderator
    board_moderator.roles = []
    return board_moderator


class Board(ModelBase):
    __tablename__ = 'board'

    id = Column(Integer(), primary_key=True)
    name = Column(String(128), unique=True, index=True, nullable=False)
    config_id = Column(Integer, ForeignKey('config.id'), nullable=False, index=True)

    config = relationship('Config', cascade='all')
    threads = relationship('Thread', backref='board', cascade='all, delete-orphan')

    moderators = association_proxy('board_moderators', 'moderator', creator=create_moderator_for_proxy)


class BoardModerator(ModelBase):
    __tablename__ = 'boardmoderator'

    board_id = Column(Integer, ForeignKey('board.id'), primary_key=True)
    moderator_id = Column(Integer, ForeignKey('moderator.id'), primary_key=True)

    roles = Column(MutableList.as_mutable(ARRAY(String)), index=True, nullable=False)

    board = relationship(Board, backref=backref('board_moderators', cascade='all, delete-orphan'))
    moderator = relationship('Moderator', backref=backref('board_moderators', cascade='all, delete-orphan'))
