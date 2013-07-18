class DjangoUserPermissionValidator(object):
    """
    Permissions Validator is used to tie into an authorization.  Is used in conjunction with the authorization decorator
    Added to the field init method.
    """
    def __init__(self, permission_name):
        self.permission_name = permission_name

    def is_write_authorized(self, ctx, target_obj, source, target):
        """
        Leverages the users has_perm(key) method to leverage the authorization.
        Only check if the source and target have changed.
        """
        user = ctx.user

        if source != target:
            return user.has_perm(self.permission_name)

        return True

    def fill_schema(self, schema_dict):
        # TODO: implement fill_schema
        pass
