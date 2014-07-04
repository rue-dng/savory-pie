import functools
import logging
import re

from django.http import HttpResponse, StreamingHttpResponse, HttpRequest
from django.db import transaction

from savory_pie.context import APIContext
from savory_pie.django import validators
from savory_pie.django.request import DjangoSavoryRequestProxy
from savory_pie.errors import AuthorizationError, PreConditionError, ResourceNotFoundError, MethodNotAllowedError
from savory_pie.formatters import JSONFormatter
from savory_pie.newrelic import set_transaction_name
from savory_pie.resources import EmptyParams
from savory_pie.helpers import get_sha1, process_get_request, process_post_request, process_put_request, process_delete_request

logger = logging.getLogger(__name__)


def batch_api_view(root_resource, base_regex):
    """
    View function factory that provides accessing to the resource tree
    rooted at root_resource.

    The produced function needs to be bound into URLs as r'^some/base/path/(.*)$'
    """
    # Hide this import from sphinx
    from django.views.decorators.csrf import csrf_exempt

    if root_resource.resource_path is None:
        root_resource.resource_path = ''

    # TODO: Make this a setter
    root_resource.set_base_regex(base_regex)

    def create_request(method, uri, user):
        request = HttpRequest()
        request.path = uri
        request.method = method.upper()
        request.user = user

        return request

    def compute_resource_path(uri, host):
        url_path = host.join(uri.split(host)[1:])
        if url_path and url_path[0] == '/':
            url_path = url_path[1:]
        pattern = re.compile(root_resource.base_regex)
        match = pattern.search(url_path)
        if match:
            base_url = match.group('base_resource')
            if base_url:
                return base_url
        return ''

    def resource_dispatch(request, uri, data, host):
        resource_path = compute_resource_path(uri, host)

        ctx = compute_context(resource_path, request, root_resource)

        resource = ctx.resolve_resource_path(resource_path)
        if resource is None:
            raise ResourceNotFoundError()

        if request.method == 'GET':
            return process_get_request(ctx, resource, data)
        elif request.method == 'POST':
            return process_post_request(ctx, resource, data)
        elif request.method == 'PUT':
            return process_put_request(ctx, resource, data)
        elif request.method == 'DELETE':
            return process_delete_request(ctx, resource)
        else:
            raise MethodNotAllowedError(method=request.method)


    @csrf_exempt
    @set_transaction_name
    def view(request, resource_path):

        ctx = compute_context(resource_path, request, root_resource)

        try:
            if resource_path or request.method != 'POST':
                return _not_found(ctx, request)

            data = ctx.formatter.read_from(request)
            result = []
            for resource_request in data.get('data', []):
                method = resource_request['method']
                uri = resource_request['uri']
                body = resource_request.get('body', None)

                resource_request = create_request(method, uri, request.user)

                result.append(
                    resource_dispatch(
                        resource_request,
                        uri,
                        body,
                        request.get_host()
                    )
                )

            return _content_success(ctx, None, request, {'data': result})

        except Exception as e:
            print e
            import traceback
            logger.exception('Caught Exception in API')
            return _internal_error(ctx, request, traceback.format_exc())

    return view


def compute_context(resource_path, request, root_resource):
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

    return ctx


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
    @set_transaction_name
    def view(request, resource_path):

        ctx = compute_context(resource_path, request, root_resource)

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
            logger.exception('Caught Exception in API')
            return _internal_error(ctx, request, traceback.format_exc())

    return view


def _strip_query_string(path):
    return path.split('?', 1)[0]


def _database_transaction(func):
    @functools.wraps(func)
    @transaction.commit_manually
    def inner(ctx, resource, request, func=func):
        try:
            response = func(ctx, resource, request)
            if 200 <= response.status_code < 300:
                transaction.commit()
            else:
                transaction.rollback()
        except:
            transaction.rollback()
            raise
        return response

    def outer(ctx, resource, request):
        try:
            return inner(ctx, resource, request)
        except transaction.TransactionManagementError:
            return _transaction_conflict(ctx, resource, request)
    return outer


def _process_get(ctx, resource, request):
    try:
        content_dict = process_get_request(
            ctx,
            resource,
            request.GET
        )
        return _content_success(ctx, resource, request, content_dict)
    except MethodNotAllowedError:
        return _not_allowed_method(ctx, resource, request)

@_database_transaction
def _process_post(ctx, resource, request):
    try:
        data = ctx.formatter.read_from(request)
        new_resource = process_post_request(
            ctx,
            resource,
            data
        )
        return _created(ctx, request, request, new_resource)
    except validators.ValidationError, ve:
        return _validation_errors(ctx, ve.resource, request, ve.errors)
    except MethodNotAllowedError:
        return _not_allowed_method(ctx, resource, request)


@_database_transaction
def _process_put(ctx, resource, request):
    try:
        data = ctx.formatter.read_from(request)
        content_dict = process_put_request(
            ctx,
            resource,
            data,
            expected_hash=request.META.get('HTTP_IF_MATCH')
        )
        if content_dict:
            return _content_success(ctx, resource, request, content_dict)
        return _no_content_success(ctx, resource, request)
    except PreConditionError:
        return _precondition_failed(ctx, resource, request)
    except MethodNotAllowedError:
        return _not_allowed_method(ctx, resource, request)
    except validators.ValidationError, ve:
        return _validation_errors(ctx, resource, request, ve.errors)
    except KeyError, ke:
        return _validation_errors(ctx, resource, request, {'missingData': ke.message})


def _process_delete(ctx, resource, request):
    try:
        process_delete_request(ctx, resource)
        return _success(ctx, request, request)
    except MethodNotAllowedError:
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
        response['ETag'] = get_sha1(ctx, content_dict)
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


def _transaction_conflict(ctx, resource, request):
    response = HttpResponse(status=409, content_type=ctx.formatter.content_type)
    error_body = {ctx.formatter.convert_to_public_property('resource'): ctx.build_resource_uri(resource)}
    ctx.formatter.write_to(error_body, response)
    return response



