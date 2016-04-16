from sqlalchemy.ext.mutable import Mutable


class MutableList(Mutable, list):
    def append(self, value):
        list.append(self, value)
        self.changed()

    def remove(self, value):
        list.remove(self, value)
        self.changed()

    @classmethod
    def coerce(cls, key, value):
        if not isinstance(value, MutableList):
            if isinstance(value, list):
                return MutableList(value)
            return Mutable.coerce(key, value)
        else:
            return value


from .board import Board
from .config import Config
from .moderator import Moderator
from .post import Post
from .report import Report
from .session import Session
from .thread import Thread
from .file import File
from .ban import Ban
from .page import Page
from .verification import Verification
