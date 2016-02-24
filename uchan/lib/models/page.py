from sqlalchemy import Column, Integer, String

from uchan.database import ModelBase


class Page(ModelBase):
    __tablename__ = 'page'

    id = Column(Integer(), primary_key=True)
    title = Column(String(), nullable=False, index=True)
    link_name = Column(String(), nullable=False, unique=True)
    type = Column(String(), nullable=False, index=True)
    order = Column(Integer(), nullable=False, index=True)
    content = Column(String(), nullable=False, index=True)
