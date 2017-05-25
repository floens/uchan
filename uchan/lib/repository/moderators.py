from typing import List

import bcrypt

from uchan.lib import roles, validation
from uchan.lib.database import session
from uchan.lib.exceptions import ArgumentError
from uchan.lib.model import ModeratorModel, BoardModel
from uchan.lib.ormmodel import ModeratorOrmModel, BoardModeratorOrmModel

MESSAGE_INVALID_USERNAME = 'Invalid username'
MESSAGE_INVALID_PASSWORD = 'Invalid password'
MESSAGE_USERNAME_IN_USE = 'This username is already in use'
MESSAGE_PASSWORD_INCORRECT = 'Password does not match'


def create_with_password(moderator: ModeratorModel, password: str):
    """
    Create a moderator account. The password is given unhashed.
    :param moderator: filled in moderator model
    :param password: password to create moderator with
    :raises ArgumentError if the username or password doesn't fit the requirements.
    See {USERNAME,PASSWORD}_{MIN,MAX}_LENGTH and {USERNAME,PASSWORD}_ALLOWED_CHARS
    :raises ArgumentError if the username is already in use. Username checking is done
    case-insensitively
    """
    if not validation.check_username_validity(moderator.username):
        raise ArgumentError(MESSAGE_INVALID_USERNAME)

    if not validation.check_password_validity(password):
        raise ArgumentError(MESSAGE_INVALID_PASSWORD)

    if find_by_username_case_insensitive(moderator.username) is not None:
        raise ArgumentError(MESSAGE_USERNAME_IN_USE)

    with session() as s:
        orm_moderator = moderator.to_orm_model()
        orm_moderator.password = _hash_password(password)
        s.add(orm_moderator)
        s.commit()


def get_all(include_boards=False) -> 'List[ModeratorModel]':
    with session() as s:
        q = s.query(ModeratorOrmModel)
        # TODO: fix this optimisation, it now requires way too many queries
        # if include_boards:
        #    q = q.options(joinedload(ModeratorOrmModel.boards.of_type(BoardOrmModel.moderators)))
        all_moderators = list(map(lambda m: ModeratorModel.from_orm_model(m, include_boards), q.all()))
        s.commit()
        return all_moderators


def find_by_username_case_insensitive(username: str) -> ModeratorModel:
    if not validation.check_username_validity(username):
        raise ArgumentError(MESSAGE_INVALID_USERNAME)

    with session() as s:
        # Username chars are safe because it is checked above
        m = s.query(ModeratorOrmModel).filter(ModeratorOrmModel.username.ilike(username)).one_or_none()
        res = None
        if m:
            res = ModeratorModel.from_orm_model(m)
        s.commit()
        return res


def find_by_id(moderator_id: int) -> ModeratorModel:
    with session() as s:
        m = s.query(ModeratorOrmModel).filter_by(id=moderator_id).one_or_none()
        res = None
        if m:
            res = ModeratorModel.from_orm_model(m)
        s.commit()
        return res


def check_password_match(moderator: ModeratorModel, password: str):
    if not validation.check_password_validity(password):
        raise ArgumentError(MESSAGE_INVALID_PASSWORD)

    with session() as s:
        moderator_orm_model = s.query(ModeratorOrmModel).filter_by(id=moderator.id).one()
        moderator_hashed_password = moderator_orm_model.password
        s.commit()

        if not bcrypt.checkpw(password.encode(), moderator_hashed_password):
            raise ArgumentError(MESSAGE_PASSWORD_INCORRECT)


def update_password(moderator: ModeratorModel, password: str):
    """
    Update a moderator password. The password is given unhashed.
    :param moderator: moderator to change password on.
    :param password: new password
    :raises ArgumentError if the password doesn't fit the requirements.
    See PASSWORD_{MIN,MAX}_LENGTH and PASSWORD_ALLOWED_CHARS
    """
    if not validation.check_password_validity(password):
        raise ArgumentError(MESSAGE_INVALID_PASSWORD)

    with session() as s:
        moderator_orm_model = s.query(ModeratorOrmModel).filter_by(id=moderator.id).one()
        moderator_orm_model.password = _hash_password(password)
        s.commit()


def delete(moderator: ModeratorModel):
    with session() as s:
        moderator_orm_model = s.query(ModeratorOrmModel).filter_by(id=moderator.id).one()
        s.delete(moderator_orm_model)
        s.commit()


def _hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())


def has_role(moderator: ModeratorModel, role: str) -> bool:
    _check_roles([role])

    with session() as s:
        moderator_orm_model = s.query(ModeratorOrmModel).filter_by(id=moderator.id).one()
        res = role in moderator_orm_model.roles
        s.commit()
        return res


def add_role(moderator: ModeratorModel, role: str):
    _check_roles([role])

    with session() as s:
        moderator_orm_model = s.query(ModeratorOrmModel).filter_by(id=moderator.id).one()
        if role in moderator_orm_model.roles:
            raise ArgumentError('Role already added')
        moderator_orm_model.roles.append(role)
        s.commit()


def remove_role(moderator: ModeratorModel, role: str):
    _check_roles([role])

    with session() as s:
        moderator_orm_model = s.query(ModeratorOrmModel).filter_by(id=moderator.id).one()
        if role not in moderator_orm_model.roles:
            raise ArgumentError('Role not added')
        moderator_orm_model.roles.remove(role)
        s.commit()


def _check_roles(role_list: 'List[str]'):
    if not all(role is not None and role in roles.ALL_ROLES for role in role_list):
        raise ArgumentError('Invalid role')
