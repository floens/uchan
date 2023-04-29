from uchan.lib.cache import cache, cache_key
from uchan.lib.database import session
from uchan.lib.model import VerificationsModel
from uchan.lib.ormmodel import VerificationOrmModel
from uchan.lib.utils import now

# TODO: configurable
VERIFICATION_DURATION = 1000 * 60 * 60 * 6


class VerifyingClient:
    def __init__(self):
        self.verification_id: str = None
        self.ip4: int = None

    @classmethod
    def from_verification_id_ip4(cls, verification_id: str, ip4: int):
        m = cls()
        m.verification_id = verification_id
        m.ip4 = ip4
        return m


def is_verified(verifying_client: VerifyingClient) -> bool:
    verification_model = None
    verification_model_cache = cache.get(
        cache_key("verifications", verifying_client.verification_id)
    )
    if verification_model_cache:
        verification_model = VerificationsModel.from_cache(verification_model_cache)

    if not verification_model:
        with session() as s:
            q = s.query(VerificationOrmModel)
            q = q.filter_by(verification_id=verifying_client.verification_id)

            verifications_orm_model = q.one_or_none()
            if verifications_orm_model:
                verification_model = VerificationsModel.from_orm_model(
                    verifications_orm_model
                )

                cached = verification_model.to_cache()
                timeout = max(1, (verification_model.expires - now()) // 1000)
                cache.set(
                    cache_key("verifications", verification_model.id),
                    cached,
                    timeout=timeout,
                )
            s.commit()

    return verification_model and _is_verifications_valid(
        verifying_client, verification_model
    )


def set_verified(verifying_client: VerifyingClient) -> VerificationsModel:
    with session() as s:
        expires = now() + VERIFICATION_DURATION

        vid = verifying_client.verification_id
        ip4 = verifying_client.ip4
        model = VerificationsModel.from_id_ip4_expires(vid, ip4, expires)
        orm_model = model.to_orm_model()

        s.add(orm_model)
        s.flush()

        m = VerificationsModel.from_orm_model(orm_model)

        s.commit()

        return m


def _is_verifications_valid(
    verifying_client: VerifyingClient, verifications: VerificationsModel
):
    time = now()

    ip_correct = verifications.ip4 == verifying_client.ip4
    expired = verifications.expires < time

    return ip_correct and not expired
