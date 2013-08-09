class DjangoUserPermissionValidator(object):
    """
    Permissions Validator is used to tie into an authorization.  Is used in conjunction with the authorization decorator
    Added to the field init method.
    """
    def __init__(self, permission_name, auth_adapter=None):
        self.permission_name = permission_name
        self.auth_adapter = auth_adapter

    def is_write_authorized(self, ctx, target_obj, source, target):
        """
        Leverages the users has_perm(key) method to leverage the authorization.
        Only check if the source and target have changed.
        """
        user = ctx.request.user

        if source != target:
            return user.has_perm(self.permission_name)

        return True

    def fill_schema(self, schema_dict):
        # TODO: implement fill_schema
        pass
