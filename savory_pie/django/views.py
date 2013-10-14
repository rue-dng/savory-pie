import hashlib
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

from django.http import HttpResponse, StreamingHttpResponse
from django.db import transaction

from savory_pie.context import APIContext
from savory_pie.errors import AuthorizationError
from savory_pie.formatters import JSONFormatter
from savory_pie.django import validators
from savory_pie.resources import EmptyParams


def api_view(root_resource):
    """
    View function factory that provides accessing to the resource tree
    rooted at root_resource.

    The produced function needs to be bound into URLs as r'^some/base/path/(.*)$'
    """
    # Hide this import from sphinx
    from django.views.decorators.csrf import csrf_exempt

    if root_resource.resource_path is None:
        root_resource.resource_path = ''

    @csrf_exempt
    def view(request, resource_path):
        full_path = _strip_query_string(request.get_full_path())
        if len(resource_path) == 0:
            base_path = full_path
        else:
            base_path = full_path[:-len(resource_path)]

        ctx = APIContext(
            base_uri=request.build_absolute_uri(base_path),
            root_resource=root_resource,
            formatter=JSONFormatter(),
            request=request
        )

        try:
            resource = ctx.resolve_resource_path(resource_path)

            if resource is None:
                return _not_found(ctx, request)

            if request.method == 'GET':
                return _process_get(ctx, resource, request)
            elif request.method == 'POST':
                return _process_post(ctx, resource, request)
            elif request.method == 'PUT':
                return _process_put(ctx, resource, request)
            elif request.method == 'DELETE':
                return _process_delete(ctx, resource, request)
            else:
                return _not_allowed_method(ctx, resource, request)
        except AuthorizationError as e:
            return _access_denied(ctx, field_name=e.name)
        except Exception:
            import traceback
            return _internal_error(ctx, request, traceback.format_exc())

    return view


def _strip_query_string(path):
    return path.split('?', 1)[0]


def _database_transaction(func):
    @transaction.commit_manually
    def inner(ctx, resource, request, func=func):
        response = func(ctx, resource, request)
        if 200 <= response.status_code < 300:
            transaction.commit()
            return response
        else:
            transaction.rollback()
            return response
    return inner


def _get_sha1(ctx, dct):
    # exclude keys like '$hash' from the hash
    dct = dict((k, v) for k, v in dct.items() if not k.startswith('$'))
    sha = hashlib.sha1()
    buf = StringIO.StringIO()
    ctx.formatter.write_to(dct, buf)
    sha.update(buf.getvalue())
    return sha.hexdigest()


def _process_get(ctx, resource, request):
    if 'GET' in resource.allowed_methods:
        content_dict = resource.get(ctx, _ParamsImpl(request.GET))
        return _content_success(ctx, resource, request, content_dict)
    else:
        return _not_allowed_method(ctx, resource, request)


@_database_transaction
def _process_post(ctx, resource, request):
    if 'POST' in resource.allowed_methods:
        try:
            new_resource = resource.post(ctx, ctx.formatter.read_from(request))
            return _created(ctx, request, request, new_resource)
        except validators.ValidationError, ve:
            return _validation_errors(ctx, ve.resource, request, ve.errors)
    else:
        return _not_allowed_method(ctx, resource, request)


@_database_transaction
def _process_put(ctx, resource, request):
    if 'PUT' in resource.allowed_methods:
        try:
            previous_content_dict = resource.get(ctx, EmptyParams())
            resource.put(ctx, ctx.formatter.read_from(request))
            # validation errors take precedence over hash mismatch
            expected_hash = request.META.get('HTTP_IF_MATCH')
            if expected_hash and expected_hash != _get_sha1(ctx, previous_content_dict):
                return _precondition_failed(ctx, resource, request)
            else:
                return _no_content_success(ctx, request, request)
        except validators.ValidationError, ve:
            return _validation_errors(ctx, resource, request, ve.errors)
        except KeyError, ke:
            return _validation_errors(ctx, resource, request, {'missingData': ke.message})
    else:
        return _not_allowed_method(ctx, resource, request)


def _process_delete(ctx, resource, request):
    if 'DELETE' in resource.allowed_methods:
        resource.delete(ctx)
        return _success(ctx, request, request)
    else:
        return _not_allowed_method(ctx, resource, request)


def _not_found(ctx, request):
    return HttpResponse(status=404)


def _access_denied(ctx, field_name=''):
    response = HttpResponse(status=403)
    ctx.formatter.write_to(
        {'validation_errors': ['Modification of field {0} not authorized'.format(field_name)]},
        response
    )
    return response


def _precondition_failed(ctx, resource, request):
    return HttpResponse(status=412)


def _not_allowed_method(ctx, resource, request):
    response = HttpResponse(status=405)
    response['Allowed'] = ','.join(resource.allowed_methods)
    return response


def _validation_errors(ctx, resource, request, errors):
    response = HttpResponse(status=400)
    ctx.formatter.write_to({'validation_errors': errors}, response)
    return response


def _created(ctx, resource, request, new_resource):
    response = HttpResponse(status=201)
    response['Location'] = ctx.build_resource_uri(new_resource)
    return response


def _content_success(ctx, resource, request, content_dict):
    if ctx.streaming_response:
        response = StreamingHttpResponse(
            content_dict,
            status=200,
            content_type=ctx.formatter.content_type)
        # No ETag, not practical on streaming
    else:
        response = HttpResponse(
            status=200,
            content_type=ctx.formatter.content_type
        )
        response['ETag'] = _get_sha1(ctx, content_dict)
        ctx.formatter.write_to(content_dict, response)
    if ctx.headers_dict:
        for header, value in ctx.headers_dict.items():
            response[header] = value

    return response


def _no_content_success(ctx, resource, request):
    return HttpResponse(status=204)


def _success(ctx, resource, request, content_dict=None):
    return HttpResponse(status=200)


def _internal_error(ctx, request, error):
    response = HttpResponse(status=500, content_type=ctx.formatter.content_type)
    error_body = {ctx.formatter.convert_to_public_property('error'): error}
    ctx.formatter.write_to(error_body, response)
    return response


class _ParamsImpl(object):
    def __init__(self, GET):
        self._GET = GET

    def keys(self):
        return self._GET.keys()

    def __contains__(self, key):
        return key in self._GET

    def __getitem__(self, key):
        return self._GET.get(key, None)

    def get(self, key, default=None):
        return self._GET.get(key, default)

    def get_as(self, key, type, default=None):
        value = self._GET.get(key, None)
        return default if value is None else type(value)

    def get_list(self, key):
        return self._GET.getlist(key)

    def get_list_of(self, key, type):
        list = self._GET.get(key, None)
        if list is None:
            return []
        else:
            return [type(x) for x in list]
