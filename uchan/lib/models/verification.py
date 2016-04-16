from sqlalchemy import Column, String, BigInteger
from sqlalchemy.dialects.postgresql import JSON

from uchan.lib.database import ModelBase


class Verification(ModelBase):
    __tablename__ = 'verification'

    verification_id = Column(String(32), primary_key=True)  # Length of a uuid4 with the - stripped
    ip4 = Column(BigInteger(), nullable=False, index=True)
    expires = Column(BigInteger(), nullable=False, index=True)
    data = Column(JSON(), nullable=False)
