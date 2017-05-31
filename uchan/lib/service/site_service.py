from uchan import app
from uchan.lib.database import session
from uchan.lib.model import SiteConfigModel
from uchan.lib.ormmodel import ConfigOrmModel, FileOrmModel, ModeratorOrmModel, SessionOrmModel, ReportOrmModel, \
    BanOrmModel, PostOrmModel, ThreadOrmModel, BoardOrmModel
from uchan.lib.repository import configs


def get_site_config() -> SiteConfigModel:
    return configs.get_site()


def update_site_config(site_config: SiteConfigModel):
    configs.update_site(site_config)


def get_model_counts():
    # No repository for this
    with session() as s:
        stats = {
            'board count': s.query(BoardOrmModel).count(),
            'thread count': s.query(ThreadOrmModel).count(),
            'post count': s.query(PostOrmModel).count(),
            'ban count': s.query(BanOrmModel).count(),
            'report count': s.query(ReportOrmModel).count(),
            'session count': s.query(SessionOrmModel).count(),
            'moderator count': s.query(ModeratorOrmModel).count(),
            'file count': s.query(FileOrmModel).count(),
            'config count': s.query(ConfigOrmModel).count()
        }
        s.commit()
        return stats


# TODO: remove
def reset_sessions():
    with session() as s:
        app.reset_sessions(s, [session.session_id])
