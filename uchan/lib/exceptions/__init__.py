class BadRequestError(Exception):
    def __init__(self, *args):
        Exception.__init__(self, *args)


class ArgumentError(ValueError):
    """Represents an error in response to a user action that has a message that can be
    displayed to the user."""

    def __init__(self, *args):
        ValueError.__init__(self, *args)
        self.message = args[0] if args else ""
