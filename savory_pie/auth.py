from datetime import datetime

import savory_pie.fields

from savory_pie.errors import AuthorizationError


def authorization_adapter(field, ctx, source_dict, target_obj):
    """
    Default adapter works on single field (non iterable)
    """
    name = field._compute_property(ctx)
    if isinstance(field, savory_pie.fields.SubObjectResourceField):
        #TODO should we move this to savory_pie.fields.SubObjectResourceField
        ##### and add _get(), to_api_value() and to_python_value() methods?
        try:    source = int(source_dict[name]['pk'])
        except: source = int(source_dict[name]['resourceUri'].split('/')[-1])
        try:    target = int(getattr(target_obj, field.name).pk)
        except: target = None
    elif field._type == datetime:
        # this allows direct comparison of datetime::datetime
        source = field.to_python_value(ctx, source_dict[name])
        target = field._get(target_obj)
    else:
        source = field.to_python_value(ctx, source_dict[name])
        target = field.to_api_value(ctx, field._get(target_obj))
    return name, source, target


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
                name, source, target = self.auth_adapter(field, ctx, source_dict, target_obj)
                if not permission.is_write_authorized(ctx, target_obj, source, target):
                    raise AuthorizationError(name)

            return fn(field, ctx, source_dict, target_obj)

        return inner
