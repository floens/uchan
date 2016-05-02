from sqlalchemy import Column, String, LargeBinary
from sqlalchemy import Integer
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship, deferred

from uchan.lib.database import ModelBase
from uchan.lib.models import MutableList, BoardModerator


def create_board_for_proxy(board):
    board_moderator = BoardModerator()
    board_moderator.board = board
    board_moderator.roles = []
    return board_moderator


class Moderator(ModelBase):
    __tablename__ = 'moderator'

    id = Column(Integer(), primary_key=True)
    username = Column(String(), unique=True)
    password = deferred(Column(LargeBinary()))

    roles = Column(MutableList.as_mutable(ARRAY(String)), index=True)

    # Bans given by this moderator
    given_bans = relationship('Ban', backref='moderator')

    posts = relationship('Post', backref='moderator')

    boards = association_proxy('board_moderators', 'board', creator=create_board_for_proxy)
