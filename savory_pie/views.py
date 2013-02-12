from django.http import HttpResponse
import json


class APIRequest(object):
    def __init__(
        self,
        http_request,
        base_uri,
        root_resource,
        resource_path,
        synthetic,

        context=None,
        method=None,
        GET=None,
        body_dict=None):

        self.http_request = http_request
        self.base_uri = base_uri
        self.root_resource = root_resource
        self.resource_path = resource_path

        self.synthetic = synthetic

        self.method = method or http_request.method
        self.GET = GET or http_request.GET
        self.context = context or dict()

        self._body_dict_cache = body_dict

    @property
    def body_dict(self):
        if self._body_dict_cache is None:
            #TODO: Add a check for MIME type
            self._body_dict_cache = json.load(self.request)

        return self._body_dict

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

    def synthetic_get(self, path_fragment, GET=None):
        return APIRequest(
            http_request=self.http_request,
            base_uri=self.base_uri,
            root_resource=self.root_resource,
            resource_path=self.resource_path + '/' + path_fragment,
            synthetic=True,
            method='GET',
            context=self.context,
            GET=GET or dict()
        )

    def synthetic_put(self, path_fragment, body_dict):
        return APIRequest(
            http_request=self.http_request,
            base_uri=self.base_uri,
            root_resource=self.root_resource,
            resource_path=self.resource_path + '/' + path_fragment,
            synthetic=False,
            method='POST',
            context=self.context,
            body_dict=body_dict
        )


def api_view(root_resource):
    def view(request, resource_path):
        full_path = _strip_query_string(request.get_full_path())
        if len(resource_path) == 0:
            base_uri = full_path
        else:
            base_uri = full_path[:-len(resource_path)]

        api_request = APIRequest(
            http_request=request,
            base_uri=base_uri,
            root_resource=root_resource,
            resource_path=resource_path,
            synthetic=False
        )
        resource = api_request.resolve_resource(full_path)

        if resource is None:
            return _process_not_found(request)

        if api_request.method == 'GET':
            return _process_get(resource, api_request)
        elif api_request.method == 'POST':
            return _process_post(resource, api_request)
        elif api_request.method == 'PUT':
            return _process_put(resource, api_request)
        elif api_request.method == 'DELETE':
            return _process_delete(resource, api_request)
        else:
            return _process_unsupported_method(resource, api_request)

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

def _serialize_to_response(dict):
    response = HttpResponse(content_type='application/json')
    json.dump(dict, response)
    return response

def _process_get(resource, api_request):
    try:
        # dereference get first, so unsupported method will be properly returned.
        get = resource.get
    except AttributeError:
        return _process_unsupported_method(resource, api_request)

    return _serialize_to_response(get(api_request))

def _process_post(resource, api_request):
    try:
        # dereference post first, so unsupported method will be properly returned.
        post = resource.post
    except AttributeError:
        return _process_unsupported_method(resource, api_request)

    post(api_request)
    return _process_success(resource, api_request)

def _process_put(resource, api_request):
    try:
        # dereference put first, so unsupported method will be properly returned.
        put = resource.put
    except AttributeError:
        return _process_unsupported_method(resource, api_request)

    new_resource = put(api_request)
    #TODO: form a valid response

def _process_delete(resource, api_request):
    try:
        delete = resource.delete
    except AttributeError:
        return _process_unsupported_method(resource, api_request)

    delete(api_request)
    return _process_success(resource, api_request)

def _process_unsupported_method(resource, api_request):
    # Ill-behaved should reply with a set of allowed actions
    return HttpResponse(status=405)

def _process_not_found(api_request):
    return HttpResponse(status=404)

def _process_success(resource, api_request):
    return HttpResponse(status=200)
