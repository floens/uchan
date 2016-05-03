import json

from sqlalchemy.orm.exc import NoResultFound
from uchan.lib import ArgumentError
from uchan.lib.configs import BoardConfig, SiteConfig
from uchan.lib.database import get_db
from uchan.lib.models.config import Config


class ConfigService:
    def __init__(self):
        pass

    def get_config_by_type(self, type):
        db = get_db()
        try:
            return db.query(Config).filter(Config.type == type).one()
        except NoResultFound:
            return None

    def load_config(self, config_row, moderator=None):
        config = self._get_config_cls(config_row.type)()

        deserialized = config_row.config

        items = []
        for config_item in config.configs:
            if moderator and not self._has_permission(moderator, config_item):
                continue

            set_value = self._search_value(config_row, deserialized, config_item.name)
            if set_value is None:
                set_value = config_item.default_value

            config_item.value = set_value

            items.append(config_item)
        config.configs = items

        return config

    def load_config_dict(self, config_row):
        config = self.load_config(config_row)

        result = {}
        for config_item in config.configs:
            result[config_item.name] = config_item.value
        return result

    def save_config(self, config, config_row):
        output = []

        for config_item in config.configs:
            output.append({
                'name': config_item.name,
                'value': config_item.value
            })

        add = False
        if config_row is None:
            config_row = Config()
            add = True
        config_row.type = config.TYPE
        config_row.config = output

        db = get_db()
        if add:
            db.add(config_row)
        db.commit()

        return config_row

    def save_from_form(self, moderator, config, config_row, form, prefix='config_'):
        for config_item in config.configs:
            if not self._has_permission(moderator, config_item):
                continue

            form_value = form.get(prefix + config_item.name, None)
            if form_value is not None:
                try:
                    config_item.set(form_value)
                except ArgumentError as e:
                    raise ArgumentError('Error setting value for {}: {}'.format(config_item.name, str(e)))
            else:
                # Unchecked checkbox
                if config_item.value_type == bool:
                    config_item.value = False

        self.save_config(config, config_row)

    def _has_permission(self, moderator, config_item):
        if config_item.access_roles:
            return any(i in moderator.roles for i in config_item.access_roles)
        else:
            return True

    def _get_config_cls(self, type):
        if type == BoardConfig.TYPE:
            return BoardConfig
        elif type == SiteConfig.TYPE:
            return SiteConfig
        else:
            raise Exception('Unknown config type')

    def _search_value(self, config_row, deserialized, name):
        for item in deserialized:
            if item['name'] == name:
                return item['value']

        return None
