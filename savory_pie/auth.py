from savory_pie.errors import AuthorizationError


def authorization_adapter(field, ctx, source_dict, target_obj):
    """
    Default adapter works on single field (non iterable)
    """
    source = field.to_python_value(ctx, source_dict[field._compute_property(ctx)])
    target = field._get(target_obj)
    return ctx, target_obj, source, target


class UserPermissionValidator(object):
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


class authorization(object):
    """
    Authorization decorator, takes a permission dictionary key and an adapter function
    @auth_adapter: an adapter function that takes ctx, source_dict, target_obj and
        returns ctx, target_obj, source, target parameters

        Use:
            @authorization(adapter)

    """
    def __init__(self, auth_adapter):
        self.auth_adapter = auth_adapter

    def __call__(self, fn):
        """
        If the user does not have an the authorization raise an AuthorizationError
        """
        def inner(field, ctx, source_dict, target_obj):
            permission = field.permission
            if permission:
                if permission.is_write_authorized(*self.auth_adapter(field, ctx, source_dict, target_obj)):
                    return fn(ctx, source_dict, target_obj)
                else:
                    raise AuthorizationError
            else:
                return fn(ctx, source_dict, target_obj)

        return inner
