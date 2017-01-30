from werkzeug.routing import BaseConverter, ValidationError

from uchan.lib.service import moderator_service


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

    def resolve_id(self, id):
        raise NotImplementedError()


class ModeratorConverter(ModelIdConverter):
    def resolve_id(self, id):
        return moderator_service.find_moderator_id(id)


def init_converters(app):
    app.url_map.converters['moderator'] = ModeratorConverter
