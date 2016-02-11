from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey
from sqlalchemy.orm import relationship

from unichan.database import ModelBase


class Post(ModelBase):
    __tablename__ = 'post'

    id = Column(Integer(), primary_key=True)

    thread_id = Column(Integer(), ForeignKey('thread.id'))
    # thread is a backref property

    report = relationship('Report', backref='post', cascade='all, delete-orphan')

    date = Column(BigInteger(), nullable=False)
    name = Column(String())
    subject = Column(String())
    text = Column(String())
    refno = Column(Integer(), nullable=False)
    password = Column(String())
