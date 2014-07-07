from StringIO import StringIO

from savory_pie.django import views
from savory_pie.tests.mock_context import mock_context as _mock_context


def savory_dispatch(root_resource, method, resource_path='', body=None, GET=None, POST=None):
    view = views.api_view(root_resource)
    request = Request(
        method=method,
        resource_path=resource_path,
        body=body,
        GET=GET,
        POST=POST
    )

    return view(request=request, resource_path=resource_path)


def savory_dispatch_batch(
        root_resource, method,
        resource_path='',
        full_host='',
        body=None,
        GET=None,
        POST=None,
        base_regex=None
):
    view = views.batch_api_view(root_resource, base_regex)
    request = Request(
        method=method,
        host=full_host,
        resource_path=resource_path,
        body=body,
        GET=GET,
        POST=POST
    )

    return view(request=request, resource_path=resource_path)


class User(object):
    email = 'savory-pie-tester@localhost'

    def is_authenticated(self):
        return True


class Request(object):
    def __init__(self, method, host='localhost', resource_path='', body=None, GET=None, POST=None):
        self.host = host
        self.resource_path = resource_path

        self.user = User()

        self.method = method
        self.body = body
        self.body_file = None

        self.GET = GET or {}
        self.POST = POST or {}
        self.META = {}
        self.REQUEST = dict(self.GET, **self.POST)

    def get_host(self):
        return self.host

    def get_full_path(self):
        return 'api/' + self.resource_path

    def build_absolute_uri(self, django_path):
        return 'http://' + self.host + '/' + django_path

    def read(self):
        if not self.body_file:
            self.body_file = StringIO(self.body)

        return self.body_file.read()


def mock_context(*args, **kwargs):
    ctx = _mock_context(*args, **kwargs)
    setattr(ctx, 'request', Request('None'))
    return ctx
