from werkzeug.routing import BaseConverter, ValidationError

from uchan.lib import validation
from uchan.lib.service import moderator_service, board_service, page_service


class ModelIdConverter(BaseConverter):
    """An url converter that resolves the id to a model and passes the model to the view.
    """

    def __init__(self, url_map):
        super().__init__(url_map)
        self.regex = '\d+'

    def to_python(self, value):
        intval = int(value)
        if not 0 < intval <= 2 ** 32:
            raise ValidationError()
        model = self.resolve_id(intval)
        if not model:
            raise ValidationError()
        return model

    def to_url(self, value):
        return str(value.id)

    def resolve_id(self, model_id):
        raise NotImplementedError()


class ModeratorConverter(ModelIdConverter):
    def resolve_id(self, moderator_id):
        return moderator_service.find_moderator_id(moderator_id)


class PageConverter(ModelIdConverter):
    def resolve_id(self, page_id):
        return page_service.find_page_id(page_id)


class BoardConverter(BaseConverter):
    def __init__(self, url_map):
        super().__init__(url_map)
        self.regex = '[^/]+'

    def to_python(self, value):
        if not validation.check_board_name_validity(value):
            raise ValidationError()
        model = board_service.find_board(value)
        if not model:
            raise ValidationError()
        return model

    def to_url(self, value):
        return str(value.name)


def init_converters(app):
    app.url_map.converters['moderator'] = ModeratorConverter
    app.url_map.converters['page'] = PageConverter
    app.url_map.converters['board'] = BoardConverter
