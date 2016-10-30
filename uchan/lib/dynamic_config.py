from uchan.lib import ArgumentError, roles


class DynamicConfigItem:
    def __init__(self, name, description, default_value, value_type, minimum=None, maximum=None, access_roles=None):
        if access_roles is None:
            access_roles = [roles.ROLE_ADMIN]

        self.name = name
        self.description = description
        self.default_value = default_value
        self.value_type = value_type
        self.value_type_name = value_type.__name__
        self.value = default_value

        self.minimum = minimum
        self.maximum = maximum

        self.access_roles = access_roles

    def set(self, raw_value):
        if self.value_type == int:
            value = None
            try:
                value = int(raw_value)
            except:
                pass

            if value is None:
                raise ArgumentError('Not a number')

            if self.minimum is not None and value < self.minimum:
                raise ArgumentError('Minimum of {}'.format(self.minimum))

            if self.maximum is not None and value > self.maximum:
                raise ArgumentError('Maximum of {}'.format(self.maximum))

            self.value = value
        elif self.value_type == str:
            value = raw_value
            if self.minimum is not None and len(value) < self.minimum:
                raise ArgumentError('Minimum length of {}'.format(self.minimum))

            if self.maximum is not None and len(value) > self.maximum:
                raise ArgumentError('Maximum length of {}'.format(self.maximum))

            self.value = value
        elif self.value_type == bool:
            self.value = raw_value == 'on'
        else:
            raise Exception('Unknown value type')


class DynamicConfig:
    TYPE = ''

    def __init__(self):
        self.configs = []

        self._values = {}

    def set_values_from_cache(self, cache_dict):
        for config in self.configs:
            if config.name in cache_dict:
                self._values[config.name] = cache_dict[config.name]
            else:
                self._values[config.name] = config.default_value

    def get(self, name):
        return self._values[name]
