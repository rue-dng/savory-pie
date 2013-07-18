from exceptions import Exception


class AuthorizationError(Exception):

    def __init__(self, name='', *args, **kwargs):
        self.name = name
        super(AuthorizationError, self).__init__(*args, **kwargs)


class SavoryPieError(Exception):
    """
    General Savory Pie Error
    """
    pass
