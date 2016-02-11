from sqlalchemy import Column, Integer, String

from unichan.database import ModelBase


class Siteconfig(ModelBase):
    __tablename__ = 'siteconfig'

    id = Column(Integer(), primary_key=True)
    config = Column(String(), nullable=False, default='{}')
