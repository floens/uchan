from sqlalchemy import Column, String, LargeBinary
from sqlalchemy import Integer
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from uchan.lib.database import ModelBase
from uchan.lib.models import MutableList


class Moderator(ModelBase):
    __tablename__ = 'moderator'

    id = Column(Integer(), primary_key=True)
    username = Column(String(), unique=True)
    password = Column(LargeBinary())

    roles = Column(MutableList.as_mutable(ARRAY(String)), index=True)

    # Bans given by this moderator
    given_bans = relationship('Ban', backref='moderator')

    posts = relationship('Post', backref='moderator')
