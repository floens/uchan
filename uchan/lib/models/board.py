from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship

from uchan.database import ModelBase

board_moderator_table = Table(
        'boardmoderator',
        ModelBase.metadata,
        Column('board_id', Integer, ForeignKey('board.id'), index=True),
        Column('moderator_id', Integer, ForeignKey('moderator.id'), index=True)
)


class Board(ModelBase):
    __tablename__ = 'board'

    id = Column(Integer(), primary_key=True)
    name = Column(String(128), unique=True, index=True, nullable=False)
    config_id = Column(Integer, ForeignKey('config.id'), nullable=False, index=True)

    config = relationship('Config', cascade='all')
    threads = relationship('Thread', backref='board', cascade='all, delete-orphan')
    moderators = relationship('Moderator', secondary=board_moderator_table, backref='boards')
