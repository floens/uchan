class BadRequestError(Exception):
    def __init__(self, *args):
        Exception.__init__(self, *args)


class NoPermissionError(Exception):
    def __init__(self, *args):
        Exception.__init__(self, *args)


class ArgumentError(ValueError):
    def __init__(self, *args):
        ValueError.__init__(self, *args)
        self.message = args[0] if args else ''
