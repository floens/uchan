from uchan.lib.database import session
from uchan.lib.model import ConfigModel
from uchan.lib.ormmodel import ConfigOrmModel


def get_config_by_type(config_type: str) -> ConfigModel:
    with session() as s:
        m = s.query(ConfigOrmModel).filter(ConfigOrmModel.type == config_type).one_or_none()
        res = None
        if m:
            res = ConfigModel.from_orm_model(m)
        return res
