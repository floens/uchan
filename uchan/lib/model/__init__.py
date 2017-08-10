from enum import unique, Enum
from typing import List

from uchan.filter.text_parser import parse_text, parse_moderator_code
from uchan.lib.ormmodel import ModeratorOrmModel, BoardOrmModel, ThreadOrmModel, BoardModeratorOrmModel, ConfigOrmModel, \
    PageOrmModel, ModeratorLogOrmModel, PostOrmModel, FileOrmModel, BanOrmModel, ReportOrmModel, VerificationOrmModel, \
    RegCodeOrmModel

"""
Plain models that don't have a connection to the database models or view models.
The data can come from orm models or caches.
Repositories accept and return these models.
"""


class PageModel:
    def __init__(self):
        self.id: int = None
        self.title: str = None
        self.link_name: str = None
        self.type: str = None
        self.order: int = None
        self.content: str = None

    def copy(self):
        m = PageModel()
        m.id = self.id
        m.title = self.title
        m.link_name = self.link_name
        m.type = self.type
        m.order = self.order
        m.content = self.content
        return m

    @classmethod
    def from_title_link_type(cls, title: str, link: str, page_type: str):
        page = PageModel()
        page.title = title
        page.link_name = link
        page.type = page_type
        page.order = 0
        page.content = ''
        return page

    @classmethod
    def from_orm_model(cls, model: PageOrmModel):
        m = cls()
        m.id = model.id
        m.title = model.title
        m.link_name = model.link_name
        m.type = model.type
        m.order = model.order
        m.content = model.content
        return m

    @classmethod
    def from_cache(cls, cache: dict):
        m = cls()
        m.id = cache['id']
        m.title = cache['title']
        m.link_name = cache['link_name']
        m.type = cache['type']
        m.order = cache['order']
        m.content = cache['content']
        return m

    def to_orm_model(self) -> PageOrmModel:
        orm_model = PageOrmModel()
        orm_model.id = self.id
        orm_model.title = self.title
        orm_model.link_name = self.link_name
        orm_model.type = self.type
        orm_model.order = self.order
        orm_model.content = self.content
        return orm_model

    def to_cache(self):
        return {
            'id': self.id,
            'title': self.title,
            'link_name': self.link_name,
            'type': self.type,
            'order': self.order,
            'content': self.content
        }


class ConfigModel:
    def __init__(self):
        self.id: int = None
        self.type: str = None
        self.config: str = None

    @classmethod
    def from_orm_model(cls, model: ConfigOrmModel):
        m = cls()
        m.id = model.id
        m.type = model.type
        m.config = model.config
        return m


class ThreadModel:
    def __init__(self):
        self.id: int = None
        self.refno: int = None
        self.last_modified: int = None
        self.refno_counter: int = None
        self.sticky: bool = None
        self.locked: bool = None

        self.posts: 'List[PostModel]' = None
        self.board: BoardModel = None

    @classmethod
    def from_orm_model(cls, model: ThreadOrmModel, include_board=False, include_posts=False, cached_thread_posts=None):
        m = cls()
        m.id = model.id
        m.refno = model.refno
        m.last_modified = model.last_modified
        m.refno_counter = model.refno_counter
        m.sticky = model.sticky
        m.locked = model.locked
        if include_board:
            m.board = BoardModel.from_orm_model(model.board)
        if include_posts:
            cached_posts_by_id = {}
            if cached_thread_posts:
                for i in cached_thread_posts:
                    cached_posts_by_id[i.id] = i

            m.posts = list(
                map(lambda i: PostModel.from_orm_model(i, cached_posts_by_id=cached_posts_by_id), model.posts))
        return m

    @classmethod
    def from_cache(cls, cache: dict):
        m = cls()
        m.id = cache['id']
        m.refno = cache['refno']
        m.last_modified = cache['last_modified']
        m.refno_counter = cache['refno_counter']
        m.sticky = cache['sticky']
        m.locked = cache['locked']
        if 'board' in cache:
            m.board = BoardModel.from_cache(cache['board'])
        if 'posts' in cache:
            m.posts = list(map(lambda i: PostModel.from_cache(i), cache['posts']))
        return m

    def to_cache(self, include_board=False, include_posts=False):
        res = {
            'id': self.id,
            'refno': self.refno,
            'last_modified': self.last_modified,
            'refno_counter': self.refno_counter,
            'sticky': self.sticky,
            'locked': self.locked
        }
        if include_board:
            res['board'] = self.board.to_cache()
        if include_posts:
            res['posts'] = list(map(lambda i: i.to_cache(), self.posts))
        return res


class BoardPageModel:
    def __init__(self):
        self.page: int = None
        self.threads: 'List[ThreadStubModel]' = None

    @classmethod
    def from_page_thread_stubs(cls, page: int, thread_stubs: 'List[ThreadStubModel]'):
        m = cls()
        m.page = page
        m.threads = thread_stubs
        return m

    @classmethod
    def from_cache(cls, cache: dict):
        m = cls()
        m.page = cache['page']
        m.threads = list(map(lambda i: ThreadStubModel.from_cache(i), cache['threads']))
        return m

    def to_cache(self):
        return {
            'page': self.page,
            'threads': list(map(lambda i: i.to_cache(), self.threads))
        }


class CatalogModel:
    def __init__(self):
        self.id: int = None

        self.threads: 'List[ThreadStubModel]' = None

    @classmethod
    def from_board_thread_stubs(cls, board: 'BoardModel', thread_stubs: 'List[ThreadStubModel]'):
        m = cls()
        m.id = board.id

        m.threads = list(map(lambda i: i.to_op_only(), thread_stubs))

        return m

    @classmethod
    def from_cache(cls, cache: dict):
        m = cls()
        m.id = cache['id']
        m.threads = list(map(lambda i: ThreadStubModel.from_cache(i), cache['threads']))
        return m

    def to_cache(self):
        return {
            'id': self.id,
            'threads': list(map(lambda i: i.to_cache(), self.threads))
        }


class ThreadStubModel:
    def __init__(self):
        self.refno: int = None
        self.last_modified: int = None
        self.sticky: bool = None
        self.locked: bool = None

        self.original_length: int = None
        self.omitted_count: int = None

        self.posts: 'List[PostModel]' = None

    @classmethod
    def from_thread(cls, thread: ThreadModel, include_snippets=False, include_op=False):
        m = cls()
        m.refno = thread.refno
        m.last_modified = thread.last_modified
        m.sticky = thread.sticky
        m.locked = thread.locked

        snippet_count = 1 if m.sticky else 5

        m.original_length = len(thread.posts)
        m.omitted_count = max(0, m.original_length - 1 - snippet_count)

        if include_snippets:
            m.posts = []
            for post in [thread.posts[0]] + thread.posts[1:][-snippet_count:]:
                copy = post.copy()
                # TODO: move outside of model logic
                maxlinestext = '<span class="abbreviated">Comment too long, view thread to read.</span>'
                copy.html_text = parse_text(copy.text, maxlines=12, maxlinestext=maxlinestext)
                m.posts.append(copy)
        if include_op:
            m.posts = [thread.posts[0]]
        return m

    @classmethod
    def from_cache(cls, cache: dict):
        m = cls()
        m.refno = cache['refno']
        m.last_modified = cache['last_modified']
        m.sticky = cache['sticky']
        m.locked = cache['locked']
        m.original_length = cache['original_length']
        m.omitted_count = cache['omitted_count']
        if 'posts' in cache:
            m.posts = list(map(lambda i: PostModel.from_cache(i), cache['posts']))
        return m

    def to_cache(self):
        r = {
            'refno': self.refno,
            'last_modified': self.last_modified,
            'sticky': self.sticky,
            'locked': self.locked,
            'original_length': self.original_length,
            'omitted_count': self.omitted_count
        }
        if self.posts:
            r['posts'] = list(map(lambda i: i.to_cache(), self.posts))
        return r

    def to_op_only(self):
        m = ThreadStubModel()
        m.refno = self.refno
        m.last_modified = self.last_modified
        m.sticky = self.sticky
        m.locked = self.locked

        m.original_length = self.original_length
        m.omitted_count = self.omitted_count

        m.posts = [self.posts[0]]

        return m


class BoardModel:
    def __init__(self):
        self.id: int = None
        self.name: str = None
        self.refno_counter: int = None

        self.config: BoardConfigModel = None

    @classmethod
    def from_name(cls, name):
        m = cls()
        m.name = name
        return m

    @classmethod
    def from_orm_model(cls, model: BoardOrmModel, include_config=True):
        m = cls()
        m.id = model.id
        m.name = model.name
        m.refno_counter = model.refno_counter
        if include_config:
            m.config = BoardConfigModel.from_orm_model(model.config)
        return m

    @classmethod
    def from_cache(cls, cache: dict):
        m = cls()
        m.id = cache['id']
        m.name = cache['name']
        m.refno_counter = cache['refno_counter']

        if 'config' in cache:
            m.config = BoardConfigModel.from_cache(cache['config'])

        return m

    def to_orm_model(self):
        orm_model = BoardOrmModel()
        orm_model.id = self.id
        orm_model.name = self.name
        orm_model.refno_counter = self.refno_counter
        return orm_model

    def to_cache(self):
        res = {
            'id': self.id,
            'name': self.name,
            'refno_counter': self.refno_counter
        }
        if self.config:
            res['config'] = self.config.to_cache()
        return res


class BoardConfigModel:
    def __init__(self):
        self.id: int = None
        self.pages: int = None
        self.per_page: int = None
        self.full_name: str = None
        self.description: str = None
        self.bump_limit: int = None
        self.file_posting: bool = None
        self.posting_verification_required: bool = None
        self.max_files: int = None

    @classmethod
    def from_defaults(cls):
        m = cls()
        m.pages = 10
        m.per_page = 15
        m.full_name = ''
        m.description = ''
        m.bump_limit = 300
        m.file_posting = True
        m.posting_verification_required = False
        m.max_files = 3
        return m

    @classmethod
    def from_orm_model(cls, model: ConfigOrmModel):
        if model.type != 'board_config':
            raise Exception('Config type incorrect')

        m = cls()
        m.id = model.id

        def g(key, default):
            for item in model.config:
                if item['name'] == key:
                    return item['value']
            return default

        m.pages = g('pages', 10)
        m.per_page = g('per_page', 15)
        m.full_name = g('full_name', '')
        m.description = g('description', '')
        m.bump_limit = g('bump_limit', 300)
        m.file_posting = g('file_posting_enabled', True)
        m.posting_verification_required = g('posting_requires_verification', False)
        m.max_files = g('max_files', 3)
        return m

    @classmethod
    def from_cache(cls, cache: dict):
        m = cls()
        m.id = cache['id']
        m.pages = cache['pages']
        m.per_page = cache['per_page']
        m.full_name = cache['full_name']
        m.description = cache['description']
        m.bump_limit = cache['bump_limit']
        m.file_posting = cache['file_posting']
        m.posting_verification_required = cache['posting_verification_required']
        m.max_files = cache['max_files'] if 'max_files' in cache else 3
        return m

    def to_orm_model(self):
        orm_model = ConfigOrmModel()
        orm_model.id = self.id
        orm_model.type = 'board_config'
        res = []

        def s(key, value, value_type):
            if type(value) != value_type:
                raise Exception('Incorrect value for board config, '
                                'expected {} for {}, got {}'.format(value_type, key, type(value)))

            res.append({
                'name': key,
                'value': value
            })

        s('pages', self.pages, int)
        s('per_page', self.per_page, int)
        s('full_name', self.full_name, str)
        s('description', self.description, str)
        s('bump_limit', self.bump_limit, int)
        s('file_posting_enabled', self.file_posting, bool)
        s('posting_requires_verification', self.posting_verification_required, bool)
        s('max_files', self.max_files, int)

        orm_model.config = res
        return orm_model

    def to_cache(self):
        return {
            'id': self.id,
            'pages': self.pages,
            'per_page': self.per_page,
            'full_name': self.full_name,
            'description': self.description,
            'bump_limit': self.bump_limit,
            'file_posting': self.file_posting,
            'posting_verification_required': self.posting_verification_required,
            'max_files': self.max_files
        }


class SiteConfigModel:
    def __init__(self):
        self.id: int = None
        self.motd: str = None
        self.footer_text: str = None
        self.boards_top: bool = None
        self.default_name: str = None
        self.posting_enabled: bool = None
        self.file_posting: bool = None

    def copy(self):
        m = SiteConfigModel()
        m.id = self.id
        m.motd = self.motd
        m.footer_text = self.footer_text
        m.boards_top = self.boards_top
        m.default_name = self.default_name
        m.posting_enabled = self.posting_enabled
        m.file_posting = self.file_posting
        return m

    @classmethod
    def from_defaults(cls):
        m = cls()
        m.motd = ''
        m.footer_text = 'Page served by [µchan](https://github.com/Floens/uchan)'
        m.boards_top = True
        m.default_name = 'Anonymous'
        m.posting_enabled = True
        m.file_posting = True
        return m

    @classmethod
    def from_orm_model(cls, model: ConfigOrmModel):
        if model.type != 'site':
            raise Exception('Config type incorrect')

        m = cls()
        m.id = model.id

        def g(key, default):
            for item in model.config:
                if item['name'] == key:
                    return item['value']
            return default

        m.motd = g('motd', '')
        m.footer_text = g('footer_text', '')
        m.boards_top = g('boards_top', '')
        m.default_name = g('default_name', 'Anonymous')
        m.posting_enabled = g('posting_enabled', True)
        m.file_posting = g('file_posting_enabled', True)

        return m

    @classmethod
    def from_cache(cls, cache: dict):
        m = cls()
        m.id = cache['id']
        m.motd = cache['motd']
        m.footer_text = cache['footer_text']
        m.boards_top = cache['boards_top']
        m.default_name = cache['default_name']
        m.posting_enabled = cache['posting_enabled']
        m.file_posting = cache['file_posting']
        return m

    def to_orm_model(self):
        orm_model = ConfigOrmModel()
        orm_model.id = self.id
        orm_model.type = 'site'
        res = []

        def s(key, value, value_type):
            if type(value) != value_type:
                raise Exception('Incorrect value for site config, '
                                'expected {} for {}, got {}'.format(value_type, key, type(value)))

            res.append({
                'name': key,
                'value': value
            })

        s('motd', self.motd, str)
        s('footer_text', self.footer_text, str)
        s('boards_top', self.boards_top, bool)
        s('default_name', self.default_name, str)
        s('posting_enabled', self.posting_enabled, bool)
        s('file_posting_enabled', self.file_posting, bool)

        orm_model.config = res
        return orm_model

    def to_cache(self):
        return {
            'id': self.id,
            'motd': self.motd,
            'footer_text': self.footer_text,
            'boards_top': self.boards_top,
            'default_name': self.default_name,
            'posting_enabled': self.posting_enabled,
            'file_posting': self.file_posting
        }


class ModeratorModel:
    def __init__(self):
        self.id: int = None
        self.username: str = None
        self.roles: 'List[str]' = []

        self.boards = None

    @classmethod
    def from_username(cls, username: str):
        m = cls()
        m.username = username
        return m

    @classmethod
    def from_orm_model(cls, model: ModeratorOrmModel, include_boards=False):
        m = cls()
        m.id = model.id
        m.username = model.username
        m.roles = list(model.roles)
        if include_boards:
            m.boards = list(map(lambda i: BoardModel.from_orm_model(i), model.boards))
        return m

    def to_orm_model(self):
        orm_model = ModeratorOrmModel()
        orm_model.username = self.username
        orm_model.roles = self.roles
        return orm_model


class BoardModeratorModel:
    def __init__(self):
        self.roles: 'List[str]' = None
        self.board: BoardModel = None
        self.moderator: ModeratorModel = None

    @classmethod
    def from_orm_model(cls, model: BoardModeratorOrmModel):
        m = cls()
        m.roles = model.roles
        m.board = BoardModel.from_orm_model(model.board)
        m.moderator = ModeratorModel.from_orm_model(model.moderator)
        return m


class ModeratorLogModel:
    def __init__(self):
        self.id: int = None
        self.date: int = None
        self.type: int = None
        self.text: str = None

        self.moderator: ModeratorModel = None
        self.board: BoardModel = None

    @classmethod
    def from_date_type_text_moderator_board(cls, date: int, type: int, text: str, moderator: ModeratorModel,
                                            board: BoardModel):
        m = cls()
        m.date = date
        m.type = type
        m.text = text

        m.moderator = moderator
        m.board = board

        return m

    @classmethod
    def from_orm_model(cls, model: ModeratorLogOrmModel, with_moderator=False, with_board=False):
        m = cls()
        m.id = model.id
        m.date = model.date
        m.type = model.type
        m.text = model.text

        if with_moderator:
            m.moderator = ModeratorModel.from_orm_model(model.moderator)
        if with_board:
            m.board = BoardModel.from_orm_model(model.board)

        return m

    def to_orm_model(self):
        orm_model = ModeratorLogOrmModel()
        orm_model.id = self.id
        orm_model.date = self.date
        orm_model.type = self.type
        orm_model.text = self.text
        if self.moderator:
            orm_model.moderator_id = self.moderator.id
        if self.board:
            orm_model.board_id = self.board.id
        return orm_model


class PostModel:
    def __init__(self):
        self.id: int = None
        self.date: int = None
        self.name: str = None
        self.subject: str = None
        self.text: str = None
        self.refno: int = None
        self.password: str = None
        self.ip4: int = None

        self.html_text: str = None
        self.mod_code: str = None

        self.thread: ThreadModel = None
        self.moderator: ModeratorModel = None
        # self.report: ReportModel = None
        self.files: List[FileModel] = None

    def copy(self):
        c = PostModel()
        c.id = self.id
        c.date = self.date
        c.name = self.name
        c.subject = self.subject
        c.text = self.text
        c.refno = self.refno
        c.password = self.password
        c.ip4 = self.ip4
        c.html_text = self.html_text
        c.mod_code = self.mod_code

        if self.files:
            c.files = c._sortfiles(list(map(lambda i: i.copy(), self.files)))

        return c

    @classmethod
    def from_orm_model(cls, model: PostOrmModel, include_thread=False, cached_posts_by_id=None):
        m = cls()
        m.id = model.id
        m.date = model.date
        m.name = model.name
        m.subject = model.subject
        m.text = model.text
        m.refno = model.refno
        m.password = model.password
        m.ip4 = model.ip4

        # We really only reuse the heavy text parser from the old cache.
        if cached_posts_by_id and m.id in cached_posts_by_id:
            m.html_text = cached_posts_by_id[m.id].html_text
        else:
            m.html_text = parse_text(m.text)

        m.mod_code = None
        if model.moderator is not None:
            m.mod_code = parse_moderator_code(model.moderator)

        if model.files:
            m.files = m._sortfiles(list(map(lambda i: FileModel.from_orm_model(i), model.files)))

        if include_thread:
            m.thread = ThreadModel.from_orm_model(model.thread, include_board=True)

        return m

    @classmethod
    def from_cache(cls, cache: dict):
        m = cls()
        m.id = cache['id']
        m.date = cache['date']
        m.name = cache['name']
        m.subject = cache['subject']
        m.text = cache['text']
        m.refno = cache['refno']
        m.password = cache['password']
        m.ip4 = cache['ip4']

        m.html_text = cache['html_text']
        m.mod_code = cache['mod_code']

        if 'files' in cache:
            m.files = m._sortfiles(list(map(lambda i: FileModel.from_cache(i), cache['files'])))

        return m

    def to_orm_model(self):
        # TODO: how to handle file, here or in the repo? and moderator?
        orm_model = PostOrmModel()
        orm_model.id = self.id
        orm_model.date = self.date
        orm_model.name = self.name
        orm_model.subject = self.subject
        orm_model.text = self.text
        orm_model.refno = self.refno
        orm_model.password = self.password
        orm_model.ip4 = self.ip4
        return orm_model

    def to_cache(self):
        res = {
            'id': self.id,
            'date': self.date,
            'name': self.name,
            'subject': self.subject,
            'text': self.text,
            'refno': self.refno,
            'password': self.password,
            'ip4': self.ip4,
            'html_text': self.html_text,
            'mod_code': self.mod_code
        }

        if self.files:
            res['files'] = list(map(lambda i: i.to_cache(), self.files))

        return res

    def _sortfiles(self, files: List['FileModel']):
        return sorted(files, key=lambda i: i.original_name)


class FileModel:
    def __init__(self):
        self.id: int = None
        self.location: str = None
        self.thumbnail_location: str = None
        self.original_name: str = None
        self.width: int = None
        self.height: int = None
        self.size: int = None
        self.thumbnail_width: int = None
        self.thumbnail_height: int = None

    def copy(self):
        c = FileModel()
        c.id = self.id
        c.location = self.location
        c.thumbnail_location = self.thumbnail_location
        c.original_name = self.original_name
        c.width = self.width
        c.height = self.height
        c.size = self.size
        c.thumbnail_width = self.thumbnail_width
        c.thumbnail_height = self.thumbnail_height
        return c

    @classmethod
    def from_orm_model(cls, model: FileOrmModel):
        m = cls()
        m.id = model.id
        m.location = model.location
        m.thumbnail_location = model.thumbnail_location
        m.original_name = model.original_name
        m.width = model.width
        m.height = model.height
        m.size = model.size
        m.thumbnail_width = model.thumbnail_width
        m.thumbnail_height = model.thumbnail_height
        return m

    @classmethod
    def from_cache(cls, cache: dict):
        m = cls()
        m.id = cache['id']
        m.location = cache['location']
        m.thumbnail_location = cache['thumbnail_location']
        m.original_name = cache['original_name']
        m.width = cache['width']
        m.height = cache['height']
        m.size = cache['size']
        m.thumbnail_width = cache['thumbnail_width']
        m.thumbnail_height = cache['thumbnail_height']
        return m

    def to_orm_model(self):
        orm_model = FileOrmModel()
        orm_model.id = self.id
        orm_model.location = self.location
        orm_model.thumbnail_location = self.thumbnail_location
        orm_model.original_name = self.original_name
        orm_model.width = self.width
        orm_model.height = self.height
        orm_model.size = self.size
        orm_model.thumbnail_width = self.thumbnail_width
        orm_model.thumbnail_height = self.thumbnail_height
        return orm_model

    def to_cache(self):
        return {
            'id': self.id,
            'location': self.location,
            'thumbnail_location': self.thumbnail_location,
            'original_name': self.original_name,
            'width': self.width,
            'height': self.height,
            'size': self.size,
            'thumbnail_width': self.thumbnail_width,
            'thumbnail_height': self.thumbnail_height
        }


class BanModel:
    def __init__(self):
        self.id: int = None
        self.ip4: int = None
        self.ip4_end: int = None
        self.reason: str = None
        self.date: int = None
        self.length: int = None
        self.board: str = None

        self.post: PostModel = None
        self.moderator: ModeratorModel = None

    @classmethod
    def from_orm_model(cls, ban: BanOrmModel, include_post=False, include_moderator=False):
        m = cls()
        m.id = ban.id
        m.ip4 = ban.ip4
        m.ip4_end = ban.ip4_end
        m.reason = ban.reason
        m.date = ban.date
        m.length = ban.length
        m.board = ban.board

        if include_post:
            m.post = PostModel.from_orm_model(ban.post) if ban.post else None

        if include_moderator:
            m.moderator = ModeratorModel.from_orm_model(ban.moderator) if ban.moderator else None

        return m

    def to_orm_model(self):
        m = BanOrmModel()
        m.id = self.id
        m.ip4 = self.ip4
        m.ip4_end = self.ip4_end
        m.reason = self.reason
        m.date = self.date
        m.length = self.length
        m.board = self.board

        # if self.post:
        #     m.post_id = self.post.id
        # if self.moderator:
        #     m.moderator_id = self.moderator.id

        return m


class ReportModel:
    def __init__(self):
        self.id: int = None
        self.count: int = None
        self.date: int = None

        self.post: PostModel = None

    @classmethod
    def from_post_count_date(cls, post: PostModel, count: int, date: int):
        m = cls()
        m.count = count
        m.date = date
        m.post = post
        return m

    @classmethod
    def from_orm_model(cls, report: ReportOrmModel):
        m = cls()
        m.id = report.id
        m.count = report.count
        m.date = report.date

        m.post = PostModel.from_orm_model(report.post, include_thread=True)

        return m

    def to_orm_model(self):
        orm_model = ReportOrmModel()
        orm_model.id = self.id
        orm_model.count = self.count
        orm_model.date = self.date

        orm_model.post_id = self.post.id

        return orm_model


class VerificationsModel:
    def __init__(self):
        self.id: str = None
        self.ip4: int = None
        self.expires: int = None

    @classmethod
    def from_id_ip4_expires(cls, verification_id: str, ip4: int, expires: int):
        m = cls()
        m.id = verification_id
        m.ip4 = ip4
        m.expires = expires
        m.verifications = {}
        return m

    @classmethod
    def from_orm_model(cls, model: VerificationOrmModel):
        m = cls()
        m.id = model.verification_id
        m.ip4 = model.ip4
        m.expires = model.expires

        m.verifications = []

        return m

    @classmethod
    def from_cache(cls, cache: dict):
        m = cls()
        m.id = cache['id']
        m.ip4 = cache['ip4']
        m.expires = cache['expires']

    def to_orm_model(self):
        orm_model = VerificationOrmModel()
        orm_model.verification_id = self.id
        orm_model.ip4 = self.ip4
        orm_model.expires = self.expires
        orm_model.data = {}

        return orm_model

    def to_cache(self):
        return {
            'id': self.id,
            'ip4': self.ip4,
            'expires': self.expires
        }


class PostResultModel:
    def __init__(self):
        self.board_name: str = None
        self.thread_refno: int = None
        self.post_refno: int = None

    @classmethod
    def from_board_name_thread_refno_post_refno(cls, board_name: str, thread_refno: int, post_refno: int):
        m = cls()
        m.board_name = board_name
        m.thread_refno = thread_refno
        m.post_refno = post_refno
        return m


class RegCodeModel:
    def __init__(self):
        self.password: bytes = None
        self.code: str = None

    @classmethod
    def from_code(cls, code: str):
        m = cls()
        m.code = code
        return m

    @classmethod
    def from_orm_model(cls, model: RegCodeOrmModel):
        m = cls()
        m.password = model.password
        m.code = model.code
        return m

    def to_orm_model(self):
        orm_model = RegCodeOrmModel()
        orm_model.password = self.password
        orm_model.code = self.code
        return orm_model


@unique
class ModeratorLogType(Enum):
    CONFIG_UPDATE = 1
    MODERATOR_INVITE = 2
    MODERATOR_REMOVE = 3
    MODERATOR_ROLE_ADD = 4
    MODERATOR_ROLE_REMOVE = 5

    REPORT_CLEAR = 6
    REPORT_POST_DELETE = 7
    REPORT_POST_DELETE_FILE = 8
