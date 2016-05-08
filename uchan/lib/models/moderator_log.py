from enum import Enum
from enum import unique

from sqlalchemy import Column, BigInteger, Integer, ForeignKey, String

from uchan.lib.database import ModelBase


@unique
class ModeratorLogType(Enum):
    CONFIG_UPDATE = 1
    MODERATOR_INVITE = 2
    MODERATOR_REMOVE = 3
    MODERATOR_ROLE_ADD = 4
    MODERATOR_ROLE_REMOVE = 5

    REPORT_CLEAR = 6
    REPORT_POST_DELETE = 7
    REPORT_POST_DELETE_FILE = 8


class ModeratorLog(ModelBase):
    __tablename__ = 'moderatorlog'

    id = Column(Integer(), primary_key=True)
    date = Column(BigInteger(), nullable=False, index=True)
    moderator_id = Column(Integer(), ForeignKey('moderator.id'), nullable=True, index=True)
    # moderator is a backref property
    board_id = Column(Integer(), ForeignKey('board.id'), nullable=True, index=True)
    # board is a backref property

    type = Column(Integer(), nullable=False, index=True)
    text = Column(String(), nullable=False)
