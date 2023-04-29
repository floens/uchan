import hashlib

from uchan.lib.database import session
from uchan.lib.exceptions import ArgumentError
from uchan.lib.model import RegCodeModel
from uchan.lib.ormmodel import RegCodeOrmModel

MESSAGE_DUPLICATE_REG_CODE = "Duplicate regcode"


def create(reg_code: RegCodeModel, password: str) -> RegCodeModel:
    reg_code.password = _hash(password)

    with session() as s:
        existing = (
            s.query(RegCodeOrmModel).filter_by(password=reg_code.password).one_or_none()
        )
        if existing:
            raise ArgumentError(MESSAGE_DUPLICATE_REG_CODE)

        orm_model = reg_code.to_orm_model()
        s.add(orm_model)
        s.flush()
        m = RegCodeModel.from_orm_model(orm_model)
        s.commit()
        return m


def find_for_password(password: str) -> RegCodeModel:
    hash_res = _hash(password)

    with session() as s:
        existing = s.query(RegCodeOrmModel).filter_by(password=hash_res).one_or_none()
        m = None
        if existing:
            m = RegCodeModel.from_orm_model(existing)
        s.commit()
        return m


def _hash(input: str):
    digest = hashlib.sha3_384()
    digest.update(input.encode("utf8"))
    return digest.digest()
