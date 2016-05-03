from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from uchan.lib.database import ModelBase


class Post(ModelBase):
    __tablename__ = 'post'

    id = Column(Integer(), primary_key=True)

    thread_id = Column(Integer(), ForeignKey('thread.id'), nullable=False, index=True)
    # thread is a backref property

    moderator_id = Column(Integer(), ForeignKey('moderator.id'), nullable=True, index=True)
    # moderator is a backref property

    report = relationship('Report', backref='post', cascade='all, delete-orphan')

    file = relationship('File', backref='post', uselist=False, lazy='joined', cascade='all, delete-orphan')

    date = Column(BigInteger(), nullable=False, index=True)
    name = Column(String())
    subject = Column(String())
    text = Column(String(), index=True)
    refno = Column(Integer(), nullable=False, index=True)
    password = Column(String())
    ip4 = Column(BigInteger(), nullable=False, index=True)
