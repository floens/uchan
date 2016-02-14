from sqlalchemy import Column, String

from unichan.database import ModelBase


class Session(ModelBase):
    __tablename__ = 'session'

    session_id = Column(String(32), primary_key=True)  # Length of a uuid4 with the - stripped
    data = Column(String(), nullable=False, index=True)
