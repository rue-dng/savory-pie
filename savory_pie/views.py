from django.http import HttpResponse
import json


class APIContext(object):
    """
    Context object passed as the second argument (after self) to Resources and Fields.

    The context object provides a hook into the underlying means to translates
    resources to / from URIs.
    """
    def __init__(self, http_request, base_path, root_resource):
        self.base_uri = http_request.build_absolute_uri(base_path)
        self.root_resource = root_resource

    def resolve_resource_uri(self, uri):
        """
        Resolves the resource that corresponds to the current URI, but only
        within the same resource tree.
        """
        if not uri.startswith(self.base_uri):
            return None

        return self.resolve_resource_path(uri[len(self.base_uri):])

    def resolve_resource_path(self, resource_path):
        """
        Resolves a resource using a resource path (not a full URI), but only
        within the same resource tree.
        """
        return _resolve_resource(
            self,
            self.root_resource,
            _split_resource_path(resource_path)
        )

    def build_resource_uri(self, resource):
        """
        Given a Resource with a resource_path, provides the correspond URI.
        Raises a ValueError if the resource_path of the Resource is None.
        """
        if resource.resource_path is None:
            raise ValueError, 'unaddressable resource'

        return self.base_uri + resource.resource_path


def api_view(root_resource):
    """
    View function factory that provides accessing to the resource tree
    rooted at root_resource.

    The produced function needs to be bound into URLs as r'^some/base/path/(.*)$'
    """
    if root_resource.resource_path is None:
        root_resource.resource_path = ''

    def view(request, resource_path):
        full_path = _strip_query_string(request.get_full_path())
        if len(resource_path) == 0:
            base_path = full_path
        else:
            base_path = full_path[:-len(resource_path)]

        ctx = APIContext(
            http_request=request,
            base_path=base_path,
            root_resource=root_resource
        )
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

    return view


def _strip_query_string(path):
    return path.split('?', 1)[0]

def _split_resource_path(resource_path):
    path_fragments = resource_path.split('/')
    if path_fragments[-1] == '':
        return path_fragments[:-1]
    else:
        return path_fragments

def _resolve_resource(ctx, root_resource, path_fragments):
    resource = root_resource
    cur_resource_path = ''

    for path_fragment in path_fragments:
        cur_resource_path = cur_resource_path + '/' + path_fragment
        resource = resource.get_child_resource(ctx, path_fragment)

        if not resource:
            return None

        if resource.resource_path is None:
            resource.resource_path = cur_resource_path

    return resource


def _deserialize_request(request):
    #TODO: Add a check for MIME type
    return json.load(request)


def _process_get(ctx, resource, request):
    if 'GET' in resource.allowed_methods:
        content_dict = resource.get(ctx, **request.GET)
        return _json_success(ctx, resource, request, content_dict)
    else:
        return _not_allowed_method(ctx, resource, request)

def _process_post(ctx, resource, request):
    if 'POST' in resource.allowed_methods:
        new_resource = resource.post(ctx, _deserialize_request(request))
        return _created(ctx, request, request, new_resource)
    else:
        return _not_allowed_method(ctx, resource, request)

def _process_put(ctx, resource, request):
    if 'PUT' in resource.allowed_methods:
        resource.put(ctx, _deserialize_request(request))
        return _success(ctx, request, request)
    else:
        return _not_allowed_method(ctx, resource, request)

def _process_delete(ctx, resource, request):
    if 'DELETE' in resource.allowed_methods:
        resource.delete()
        return _success(ctx, request, request)
    else:
        return _not_allowed_method(ctx, resource, request)


def _not_found(ctx, request):
    return HttpResponse(status=404)

def _not_allowed_method(ctx, resource, request):
    response = HttpResponse(status=405)
    response['Allowed'] = ','.join(resource.allowed_methods)
    return response

def _created(ctx, resource, request, new_resource):
    response = HttpResponse(status=201)
    response['Location'] = ctx.build_resource_uri(new_resource)
    return response

def _json_success(ctx, resource, request, content_dict):
    response = HttpResponse(status=200, content_type='application/json')
    json.dump(content_dict, response)
    return response

def _no_content_success(ctx, resource, request):
    return HttpResponse(status=204)

def _success(ctx, resource, request, content_dict=None):
    return HttpResponse(status=200)

