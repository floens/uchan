import json

from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship

from unichan.database import ModelBase
from unichan.lib.board_config import BoardConfig

board_moderator_table = Table(
        'boardmoderator',
        ModelBase.metadata,
        Column('board_id', Integer, ForeignKey('board.id')),
        Column('moderator_id', Integer, ForeignKey('moderator.id'))
)


class Board(ModelBase):
    __tablename__ = 'board'

    id = Column(Integer(), primary_key=True)
    name = Column(String(128), unique=True, index=True, nullable=False)
    config = Column(String(), nullable=False, default='{}')

    threads = relationship('Thread', backref='board', cascade='all, delete-orphan')

    moderators = relationship('Moderator', secondary=board_moderator_table, backref='boards')

    def get_dynamic_config(self):
        board_config = BoardConfig()
        board_config.deserialize(self.config)
        return board_config

    def get_config_dict(self):
        result = {}
        for item in json.loads(self.config):
            result[item['name']] = item['value']
        return result
