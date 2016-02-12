import string

import bcrypt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from unichan.database import get_db
from unichan.lib.models import Moderator


class ModeratorService:
    USERNAME_MAX_LENGTH = 50
    USERNAME_ALLOWED_CHARS = string.ascii_letters + string.digits + '_'
    PASSWORD_MAX_LENGTH = 50
    PASSWORD_ALLOWED_CHARS = string.ascii_letters + string.digits + '_'

    def __init__(self, cache):
        self.cache = cache

    def check_username_validity(self, username):
        if not 0 < len(username) <= self.USERNAME_MAX_LENGTH:
            return False

        if not all(c in self.USERNAME_ALLOWED_CHARS for c in username):
            return False

        return True

    def check_password_validity(self, password):
        if not 0 < len(password) <= self.PASSWORD_MAX_LENGTH:
            return False

        if not all(c in self.PASSWORD_ALLOWED_CHARS for c in password):
            return False

        return True

    def create_moderator(self, moderator, password):
        if not self.check_username_validity(moderator.username):
            raise ValueError('Invalid username')

        if not self.check_password_validity(password):
            raise ValueError('Invalid password')

        moderator.password = self.hash_password(password)

        db = get_db()
        db.add(moderator)
        try:
            db.commit()
        except IntegrityError:
            raise ValueError('Duplicate username')

    def find_moderator_id(self, id):
        db = get_db()
        try:
            return db.query(Moderator).filter_by(id=id).one()
        except NoResultFound:
            return None

    def find_moderator_username(self, username):
        db = get_db()
        try:
            return db.query(Moderator).filter_by(username=username).one()
        except NoResultFound:
            return None

    def get_all_moderators(self):
        return get_db().query(Moderator).all()

    def has_role(self, moderator, role):
        return role is not None and role in moderator.roles

    def moderates_board(self, moderator, board):
        return board in moderator.boards

    def check_password(self, moderator, password):
        moderator_hashed_password = moderator.password

        if bcrypt.hashpw(password.encode(), moderator_hashed_password) != moderator_hashed_password:
            raise ValueError('Password does not match')

    def hash_password(self, password):
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt())
