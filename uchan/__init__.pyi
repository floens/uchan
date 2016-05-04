# Type checking
# Done here because the imports can't be loaded at this stage

import logging

from celery import Celery
from flask import Flask

from uchan.lib import database
from uchan.lib.cache import BoardCache
from uchan.lib.cache import CacheWrapper
from uchan.lib.cache import PageCache
from uchan.lib.cache import PostsCache
from uchan.lib.cache import SiteCache
from uchan.lib.plugin_manager import PluginManager
from uchan.lib.action_authorizer import ActionAuthorizer
from uchan.lib.service import BanService
from uchan.lib.service import BoardService
from uchan.lib.service import ConfigService
from uchan.lib.service import FileService
from uchan.lib.service import ModeratorService
from uchan.lib.service import PageService
from uchan.lib.service import PostsService
from uchan.lib.service import VerificationService
from uchan.lib.service import ReportService


# TODO: The @property methods are a workaround for type checking to work. bug in intellij?
class Globals:
    def __init__(self):
        self._logger = None  # type: logging.Logger
        self._mod_logger = None  # type: logging.Logger
        self._app = None  # type: Flask
        self._celery = None  # type: Celery
        self._database = None  # type: database
        self._plugin_manager = None  # type: PluginManager
        self._action_authorizer = None  # type: ActionAuthorizer

        self._cache = None  # type: CacheWrapper
        self._posts_cache = None  # type: PostsCache
        self._board_cache = None  # type: BoardCache
        self._site_cache = None  # type: SiteCache
        self._page_cache = None  # type: PageCache

        self._posts_service = None  # type:PostsService
        self._board_service = None  # type: BoardService
        self._moderator_service = None  # type:ModeratorService
        self._config_service = None  # type:ConfigService
        self._file_service = None  # type:FileService
        self._ban_service = None  # type:BanService
        self._page_service = None  # type:PageService
        self._verification_service = None  # type: VerificationService
        self._report_service = None  # type: ReportService

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def mod_logger(self) -> logging.Logger:
        return self._mod_logger

    @property
    def app(self) -> Flask:
        return self._app

    @property
    def celery(self) -> Celery:
        return self._celery

    @property
    def database(self) -> database:
        return self._database

    @property
    def plugin_manager(self) -> PluginManager:
        return self._plugin_manager

    @property
    def action_authorizer(self) -> ActionAuthorizer:
        return self._action_authorizer

    @property
    def cache(self) -> CacheWrapper:
        return self._cache

    @property
    def posts_cache(self) -> PostsCache:
        return self._posts_cache

    @property
    def board_cache(self) -> BoardCache:
        return self._board_cache

    @property
    def site_cache(self) -> SiteCache:
        return self._site_cache

    @property
    def page_cache(self) -> PageCache:
        return self._page_cache

    @property
    def posts_service(self) -> PostsService:
        return self._posts_service

    @property
    def board_service(self) -> BoardService:
        return self._board_service

    @property
    def moderator_service(self) -> ModeratorService:
        return self._moderator_service

    @property
    def config_service(self) -> ConfigService:
        return self._config_service

    @property
    def file_service(self) -> FileService:
        return self._file_service

    @property
    def ban_service(self) -> BanService:
        return self._ban_service

    @property
    def page_service(self) -> PageService:
        return self._page_service

    @property
    def verification_service(self) -> VerificationService:
        return self._verification_service

    @property
    def report_service(self) -> ReportService:
        return self._report_service
