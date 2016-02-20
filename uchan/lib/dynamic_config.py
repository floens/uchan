from uchan.lib import ArgumentError


class DynamicConfigItem:
    def __init__(self, name, description, default_value, value_type, minimum=None, maximum=None):
        self.name = name
        self.description = description
        self.default_value = default_value
        self.value_type = value_type
        self.value_type_name = value_type.__name__
        self.value = default_value

        self.minimum = minimum
        self.maximum = maximum

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

    def get(self, key):
        for item in self.configs:
            if item.name == key:
                return item.value
        return None

    def set(self, key, value):
        for item in self.configs:
            if item.nam == key:
                item.set(value)

        raise KeyError()
