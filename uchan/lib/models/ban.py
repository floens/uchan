from sqlalchemy import Column, Integer, ForeignKey, String, BigInteger

from uchan.lib.database import ModelBase


class Ban(ModelBase):
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
