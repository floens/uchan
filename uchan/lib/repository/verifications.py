from uchan.lib.database import session
from uchan.lib.model import VerificationsModel
from uchan.lib.ormmodel import VerificationOrmModel
from uchan.lib.utils import now


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


def get_verified(verifying_client: VerifyingClient, name: str) -> bool:
    res = False

    with session() as s:
        q = s.query(VerificationOrmModel)
        q = q.filter_by(id=verifying_client.verification_id)

        verifications_orm_model = q.one_or_none()
        if verifications_orm_model:
            verifications = VerificationsModel.from_orm_model(verifications_orm_model)

            if not _are_verifications_valid(verifying_client, verifications):
                s.delete(verifications_orm_model)
            else:
                verification = verifications.get(name)
                if verification and verification.verified:
                    res = True

        s.commit()

    return res


def _are_verifications_valid(verifying_client: VerifyingClient, verifications: VerificationsModel):
    time = now()

    ip_correct = verifications.ip4 == verifying_client.ip4
    expired = verifications.expires < time

    return ip_correct and not expired
