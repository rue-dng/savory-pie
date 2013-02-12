from savory_pie.views import APIRequest

def mock_get(GET=None):
    return APIRequest(
        http_request=HttpRequest(method='GET', GET=GET),
        base_uri='',
        root_resource=None,
        resource_path='',
        synthetic=False
    )

def mock_put(body_dict=None):
    return APIRequest(
        http_request=HttpRequest(method='PUT', body_dict=body_dict),
        base_uri='',
        root_resource=None,
        resource_path='',
        synthetic=False
    )

def mock_post(body_dict=None):
    return APIRequest(
        http_request=HttpRequest(method='POST', body_dict=body_dict),
        base_uri='',
        root_resource=None,
        resource_path='',
        synthetic=False
    )

def mock_delete():
    return APIRequest(
        http_request=HttpRequest(method='DELETE', body_dict=body_dict),
        base_uri='',
        root_resource=None,
        resource_path='',
        synthetic=False
    )

class HttpRequest(object):
    def __init__(self, method, host='localhost', path='', body=None, GET=None, POST=None):
        self.host = host
        self.path = path

        self.method = method
        self.body = body
        self.body_file = None

        self.GET = GET or dict()
        self.POST = POST or dict()
        self.REQUEST = dict(self.GET, **self.POST)

    def get_full_path(self):
        return 'http://' + self.host + '/' + self.path

    def read(self):
        if not self.body_file:
            self.body_file = StringIO(self.body)

        return self.body_file.read()
