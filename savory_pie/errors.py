from exceptions import Exception


class AuthorizationError(Exception):

    def __init__(self, name='', *args, **kwargs):
        self.name = name
        super(AuthorizationError, self).__init__(*args, **kwargs)


class MethodNotAllowedError(Exception):

    def __init__(self, method='', *args, **kwargs):
        self.method = method
        super(MethodNotAllowedError, self).__init__(*args, **kwargs)


class PreConditionError(Exception):
    pass


class ResourceNotFoundError(Exception):
    pass


class SavoryPieError(Exception):
    """
    General Savory Pie Error
    """
    pass
