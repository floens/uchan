from sqlalchemy import Column, Integer, ForeignKey, String

from unichan.database import ModelBase


class File(ModelBase):
    __tablename__ = 'file'

    id = Column(Integer(), primary_key=True)
    location = Column(String(), nullable=False)
    thumbnail_location = Column(String(), nullable=False)
    post_id = Column(Integer(), ForeignKey('post.id'), nullable=False)
    # post is a backref property
    original_name = Column(String(), nullable=False)
    width = Column(Integer(), nullable=False)
    height = Column(Integer(), nullable=False)
    size = Column(Integer(), nullable=False)
    thumbnail_width = Column(Integer(), nullable=False)
    thumbnail_height = Column(Integer(), nullable=False)
