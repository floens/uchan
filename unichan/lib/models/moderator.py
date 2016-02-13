from sqlalchemy import Column, String, LargeBinary
from sqlalchemy import Integer
from sqlalchemy.dialects.postgresql import ARRAY

from unichan.database import ModelBase
from unichan.lib.models import MutableList


class Moderator(ModelBase):
    __tablename__ = 'moderator'

    id = Column(Integer(), primary_key=True)
    username = Column(String(), unique=True)
    password = Column(LargeBinary())

    roles = Column(MutableList.as_mutable(ARRAY(String)), index=True)
