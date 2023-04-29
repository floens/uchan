from uchan.lib.cache import LocalCache, cache, cache_key
from uchan.lib.database import session
from uchan.lib.model import SiteConfigModel
from uchan.lib.ormmodel import ConfigOrmModel

MESSAGE_SITE_CONFIG_EXISTS = "Site config already exists"

# def create_site(site_config: SiteConfigModel):
#     with session() as s:
#         exiting = s.query(ConfigOrmModel).filter_by(type='site').one_or_none()
#         if exiting:
#             raise ArgumentError(MESSAGE_SITE_CONFIG_EXISTS)
#
#         m = site_config.to_orm_model()
#         s.add(m)
#         r = SiteConfigModel.from_orm_model(m)
#         s.commit()
#         return r


local_site_config_cache = LocalCache()


def update_site(site_config: SiteConfigModel):
    with session() as s:
        s.merge(site_config.to_orm_model())
        s.commit()
        cache.set(cache_key("config_site"), site_config.to_cache())


def get_site() -> SiteConfigModel:
    local_cached = local_site_config_cache.get("site_config")
    if local_cached:
        return local_cached.copy()

    cached = cache.get(cache_key("config_site"))
    if cached:
        res = SiteConfigModel.from_cache(cached)
    else:
        with session() as s:
            m = s.query(ConfigOrmModel).filter_by(type="site").one_or_none()
            if m:
                res = SiteConfigModel.from_orm_model(m)
            else:
                res = SiteConfigModel.from_defaults()
            s.commit()

            cache.set(cache_key("config_site"), res.to_cache())

    local_site_config_cache.set("site_config", res)
    return res
