from sqlalchemy import Column, String, LargeBinary
from sqlalchemy import Integer
from sqlalchemy.dialects import postgresql

from unichan.database import ModelBase


class Moderator(ModelBase):
    __tablename__ = 'moderator'

    id = Column(Integer(), primary_key=True)
    username = Column(String(), unique=True)
    password = Column(LargeBinary())

    roles = Column(postgresql.ARRAY(String), index=True)
