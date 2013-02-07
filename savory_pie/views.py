import json

def service_dispatcher(root_resource):
    def view(request):
        resource = _resolve_resource(root_resource, [])
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

def _resolve_resource(resource, path_fragments):
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
        get = getattr(resource, 'get')
        return _serialize_to_response(get(**request.GET))
    except KeyError:
        return _process_unsupported_method(resource, request)

def _process_post(resource, request):
    try:
        post = getattr(resource, 'post')
        post(_deserialize_request(request))
    except KeyError:
        return _process_unsupported_method(resource, request)

def _process_put(resource, request):
    try:
        put = getattr(resource, 'put')
        new_resource = put(_deserialize_request(request))
    except KeyError:
        return _process_unsupported_method(resource, request)

def _process_delete(resource, request):
    try:
        delete = getattr(resource, 'delete')
        delete()
    except KeyError:
        return _process_unsupported_method(resource, request)

def _process_unsupported_method(resource, request):
    # Ill-behaved should reply with a set of allowed actions
    return HttpResponse(status=405)