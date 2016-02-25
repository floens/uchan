from sqlalchemy import Column, Integer, ForeignKey, BigInteger

from uchan.lib.database import ModelBase


class Report(ModelBase):
    __tablename__ = 'report'

    id = Column(Integer(), primary_key=True)
    post_id = Column(Integer(), ForeignKey('post.id'), nullable=False, index=True)
    # post is a backref property
    count = Column(Integer(), nullable=False)
    date = Column(BigInteger(), nullable=False, index=True)
