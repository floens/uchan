from typing import Type

from sqlalchemy.orm.exc import NoResultFound

from uchan.lib.dynamic_config import DynamicConfig
from uchan.lib.exceptions import ArgumentError
from uchan.lib.configs import BoardConfig, SiteConfig
from uchan.lib.database import get_db
from uchan.lib.model import ConfigModel
from uchan.lib.ormmodel import ConfigOrmModel
from uchan.lib.repository import configs


def load_config_by_type(config_type: str) -> DynamicConfig:
    res = configs.get_config_by_type(config_type)
    if res:
        return load_config(res)


def get_config_by_type(config_type):
    return configs.get_config_by_type(config_type)


def load_config(config_model: ConfigModel, moderator=None) -> DynamicConfig:
    config: DynamicConfig = _get_config_cls(config_model.type)()

    deserialized = config_model.config

    items = []
    for config_item in config.configs:
        if moderator and not _has_permission(moderator, config_item):
            continue

        set_value = _search_value(config_model, deserialized, config_item.name)
        if set_value is None:
            set_value = config_item.default_value

        config_item.value = set_value

        items.append(config_item)
    config.configs = items

    return config


def load_config_dict(config_row):
    config = load_config(config_row)

    result = {}
    for config_item in config.configs:
        result[config_item.name] = config_item.value
    return result


def save_config(config, config_row):
    output = []

    for config_item in config.configs:
        output.append({
            'name': config_item.name,
            'value': config_item.value
        })

    add = False
    if config_row is None:
        config_row = ConfigOrmModel()
        add = True
    config_row.type = config.TYPE
    config_row.config = output

    db = get_db()
    if add:
        db.add(config_row)
    db.commit()

    return config_row


def save_from_form(moderator, config, config_row, form, prefix='config_'):
    for config_item in config.configs:
        if not _has_permission(moderator, config_item):
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

    save_config(config, config_row)


def _has_permission(moderator, config_item):
    if config_item.access_roles:
        return any(i in moderator.roles for i in config_item.access_roles)
    else:
        return True


def _get_config_cls(config_type) -> 'Type[DynamicConfig]':
    if config_type == BoardConfig.TYPE:
        return BoardConfig
    elif config_type == SiteConfig.TYPE:
        return SiteConfig
    else:
        raise Exception('Unknown config type')


def _search_value(config_row, deserialized, name):
    for item in deserialized:
        if item['name'] == name:
            return item['value']

    return None
