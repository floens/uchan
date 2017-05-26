from typing import List, Any

from flask import request, url_for


class PagedModel:
    def __init__(self):
        self.cached_count: int = None

    def header(self):
        raise NotImplementedError()

    def row(self, model):
        raise NotImplementedError()

    def provide_count(self) -> int:
        raise NotImplementedError()

    def provide_data(self, offset: int, limit: int) -> List[Any]:
        raise NotImplementedError()

    def count(self) -> int:
        if self.cached_count is None:
            self.cached_count = self.provide_count()
        return self.cached_count

    def data(self, name):
        offset = self.offset(name)
        limit = self.limit()

        return self.provide_data(offset, limit)

    def offset(self, name):
        offset_key = name + '_offset'

        return max(0, request.args.get(offset_key, type=int, default=0))

    def limit(self):
        return 10

    def pages(self, name):
        offset = self.offset(name)
        limit = self.limit()
        count = self.count()

        last_page = (max(count - 1, 0)) // limit

        current_page = offset // limit

        def p(page):
            return {
                'text': str(page + 1),
                'offset': page * limit,
                'is_current': page == current_page
            }

        yield p(0)
        for i in range(current_page - 5, current_page + 5):
            if 1 <= i < last_page:
                yield p(i)
        if last_page != 0:
            yield p(last_page)

    def has_previous(self, name):
        return self.offset(name) > 0

    def has_next(self, name):
        return self.offset(name) + self.limit() < self.count()

    def previous_link(self, name, base_url):
        return self.offset_link(name, base_url, self.offset(name) - self.limit())

    def next_link(self, name, base_url):
        return self.offset_link(name, base_url, self.offset(name) + self.limit())

    def offset_link(self, name, base_url, offset):
        d = {}
        if offset > 0:
            d[name + '_offset'] = str(offset)
        return url_for(base_url, **d)
