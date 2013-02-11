from django.http import HttpResponse
import json


class APIContext(object):
    def resolve_resource(self, uri):
        pass

    def build_absolute_uri(self, resource):
        pass


def api_view(root_resource):
    def view(request, resource_path):
        resource = _resolve_resource(root_resource, _split_resource_path(resource_path))

        if resource is None:
            return _process_not_found(request)

        if request.method == 'GET':
            return _process_get(resource, request)
        elif request.method == 'POST':
            return _process_post(resource, request)
        elif request.method == 'PUT':
            return _process_put(resource, request)
        elif request.method == 'DELETE':
            return _process_delete(resource, request)
        else:
            return _process_unsupported_method(resource, request)

    return view

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

def _process_get(resource, request):
    try:
        # dereference get first, so unsupported method will be properly returned.
        get = resource.get
    except AttributeError:
        return _process_unsupported_method(resource, request)
    return _serialize_to_response(get(**request.GET))

def _process_post(resource, request):
    try:
        # dereference post first, so unsupported method will be properly returned.
        post = resource.post
    except AttributeError:
        return _process_unsupported_method(resource, request)
    post(_deserialize_request(request))
    return _process_success(request, request)

def _process_put(resource, request):
    try:
        # dereference put first, so unsupported method will be properly returned.
        put = resource.put
    except AttributeError:
        return _process_unsupported_method(resource, request)
    new_resource = put(_deserialize_request(request))
    #TODO: form a valid response

def _process_delete(resource, request):
    try:
        resource.delete()
        return _process_success(resource, request)
    except AttributeError:
        return _process_unsupported_method(resource, request)

def _process_unsupported_method(resource, request):
    # Ill-behaved should reply with a set of allowed actions
    return HttpResponse(status=405)

def _process_not_found(request):
    return HttpResponse(status=404)

def _process_success(resource, request):
    return HttpResponse(status=200)
