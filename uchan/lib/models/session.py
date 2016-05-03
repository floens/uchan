from sqlalchemy import Column, String, BigInteger
from sqlalchemy.dialects.postgresql import JSON

from uchan.lib.database import ModelBase


class Session(ModelBase):
    __tablename__ = 'session'

    session_id = Column(String(32), primary_key=True)  # Length of a uuid4 with the - stripped
    data = Column(JSON(), nullable=False)
    expires = Column(BigInteger(), nullable=False, index=True)
