import hashlib

from collections import OrderedDict
from .errors import MethodNotAllowedError, PreConditionError
from .resources import EmptyParams, _ParamsImpl

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO


def get_sha1(ctx, dct):
    # exclude keys like '$hash' from the hash
    hash_dict = OrderedDict()
    for key in dct.keys():
        if not key.startswith('$'):
            # Do not hash the magic variables
            hash_dict[key] = dct[key]

    buf = StringIO.StringIO()
    ctx.formatter.write_to(hash_dict, buf)

    return _hash_string(buf.getvalue())


def process_get_request(ctx, resource, get_params):
    if 'GET' in resource.allowed_methods:
        return resource.get(ctx, _ParamsImpl(get_params))
    else:
        raise MethodNotAllowedError(method='GET')


def process_post_request(ctx, resource, data):
    if 'POST' in resource.allowed_methods:
        return resource.post(ctx, data)
    else:
        raise MethodNotAllowedError(method='POST')


def process_put_request(ctx, resource, data, expected_hash=None):
    if 'PUT' in resource.allowed_methods:
        previous_content_dict = resource.get(ctx, EmptyParams())
        content_dict = resource.put(ctx, data,)
        # validation errors take precedence over hash mismatch
        if expected_hash and expected_hash != get_sha1(ctx, previous_content_dict):
            raise PreConditionError()
        else:
            return content_dict
    else:
        raise MethodNotAllowedError(method='PUT')


def process_delete_request(ctx, resource):
    if 'DELETE' in resource.allowed_methods:
        resource.delete(ctx)
    else:
        raise MethodNotAllowedError(method='DELETE')


def _hash_string(value):
    sha = hashlib.sha1(value)
    return sha.hexdigest()
