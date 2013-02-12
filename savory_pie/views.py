from django.http import HttpResponse
import json


class APIContext(object):
    def __init__(self, http_request, base_uri, root_resource):
        self.http_request = http_request
        self.base_uri = base_uri
        self.root_resource = root_resource

    def resolve_resource(self, uri):
        if not uri.startswith(self.base_uri):
            return None

        resource_path = uri[len(self.base_uri):]
        return _resolve_resource(
            self.root_resource,
            _split_resource_path(resource_path)
        )

    def build_absolute_uri(self, resource_path, path_addition=None):
        if path_addition:
            resource_path = resource_path + '/' + path_addition

        return self.http_request.build_absolute_uri(resource_path)


def api_view(root_resource):
    def view(request, resource_path):
        full_path = _strip_query_string(request.get_full_path())
        if len(resource_path) == 0:
            base_uri = full_path
        else:
            base_uri = full_path[:-len(resource_path)]

        ctx = APIContext(
            http_request=request,
            base_uri=base_uri,
            root_resource=root_resource
        )
        resource = ctx.resolve_resource(full_path)

        if resource is None:
            return _process_not_found(ctx, request)

        if request.method == 'GET':
            return _process_get(ctx, resource, request)
        elif request.method == 'POST':
            return _process_post(ctx, resource, request)
        elif request.method == 'PUT':
            return _process_put(ctx, resource, request)
        elif request.method == 'DELETE':
            return _process_delete(ctx, resource, request)
        else:
            return _process_unsupported_method(ctx, resource, request)

    return view

def _strip_query_string(path):
    query_string_pos = path.find('?')
    if query_string_pos == -1:
        return path
    else:
        return path[:query_string_pos]

def _split_resource_path(resource_path):
    path_fragments = resource_path.split('/')
    if path_fragments[-1] == '':
        return path_fragments[:-1]
    else:
        return path_fragments

def _resolve_resource(root_resource, path_fragments):
    resource = root_resource
    for path_fragment in path_fragments:
        resource = resource.get_child_resource(path_fragment)
        if not resource:
            return None
    return resource

def _deserialize_request(request):
    #TODO: Add a check for MIME type
    return json.load(request)

def _serialize_to_response(dict):
    response = HttpResponse(content_type='application/json')
    json.dump(dict, response)
    return response

def _process_get(ctx, resource, request):
    try:
        # dereference get first, so unsupported method will be properly returned.
        get = resource.get
    except AttributeError:
        return _process_unsupported_method(ctx, resource, request)

    return _serialize_to_response(get(ctx, **request.GET))

def _process_post(ctx, resource, request):
    try:
        # dereference post first, so unsupported method will be properly returned.
        post = resource.post
    except AttributeError:
        return _process_unsupported_method(ctx, resource, request)

    post(ctx, _deserialize_request(request))
    return _process_success(ctx, request, request)

def _process_put(ctx, resource, request):
    try:
        # dereference put first, so unsupported method will be properly returned.
        put = resource.put
    except AttributeError:
        return _process_unsupported_method(ctx, resource, request)

    new_resource = put(ctx, _deserialize_request(request))
    #TODO: form a valid response

def _process_delete(ctx, resource, request):
    try:
        delete = resource.delete
    except AttributeError:
        return _process_unsupported_method(ctx, resource, request)

    delete(ctx)
    return _process_success(ctx, resource, request)

def _process_unsupported_method(ctx, resource, request):
    # Ill-behaved should reply with a set of allowed actions
    return HttpResponse(status=405)

def _process_not_found(ctx, request):
    return HttpResponse(status=404)

def _process_success(ctx, resource, request):
    return HttpResponse(status=200)
