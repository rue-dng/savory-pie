import unittest
from StringIO import StringIO

from mock import Mock
from savory_pie import views


def mock_resource(name=None, resource_path=None, child_resource=None):
    resource = Mock(name=name, spec=[])
    resource.resource_path = resource_path

    resource.allowed_methods = set()
    resource.get = Mock(name='get')
    resource.post = Mock(name='post')
    resource.put = Mock(name='put')
    resource.delete = Mock(name='delete')

    resource.get_child_resource = Mock(return_value=child_resource)

    return resource


def dispatch(root_resource, method, resource_path='', body=None, GET=None, POST=None):
    view = views.api_view(root_resource)
    request = Request(
        method=method,
        path='api/' + resource_path,
        body=body,
        GET=GET,
        POST=POST
    )

    return view(request=request, resource_path=resource_path)


class Request(object):
    def __init__(self, method, host='localhost', path='', body=None, GET=None, POST=None):
        self.host = host
        self.path = path

        self.method = method
        self.body = body
        self.body_file = None

        self.GET = GET or {}
        self.POST = POST or {}
        self.REQUEST = dict(self.GET, **self.POST)

    def get_full_path(self):
        return 'api/' + self.path

    def build_absolute_uri(self, django_path):
        return 'http://' + self.host + '/' + django_path

    def read(self):
        if not self.body_file:
            self.body_file = StringIO(self.body)

        return self.body_file.read()


class ViewTest(unittest.TestCase):
    def test_get_success(self):
        root_resource = mock_resource(name='root')
        root_resource.allowed_methods.add('GET')
        root_resource.get = Mock(return_value={'foo': 'bar'})

        response = dispatch(root_resource, method='GET')
        self.assertEqual(response.content, '{"foo": "bar"}')

        self.assertTrue(root_resource.get.called)

    def test_get_not_supported(self):
        root_resource = mock_resource(name='root')

        response = dispatch(root_resource, method='GET')
        self.assertEqual(response.status_code, 405)

    def test_put_success(self):
        root_resource = mock_resource(name='root')
        root_resource.allowed_methods.add('PUT')

        dispatch(root_resource, method='PUT', body='{}')

        self.assertTrue(root_resource.put.called)

    def test_put_not_supported(self):
        root_resource = mock_resource(name='root')

        response = dispatch(root_resource, method='PUT')
        self.assertEqual(response.status_code, 405)

    def test_post_success(self):
        root_resource = mock_resource(name='root')
        root_resource.allowed_methods.add('POST')

        new_resource = mock_resource(name='new', resource_path='foo')
        root_resource.post = Mock(return_value=new_resource)

        dispatch(root_resource, method='POST', body='{}')

        self.assertTrue(root_resource.post.called)

    def test_post_not_supported(self):
        root_resource = mock_resource(name='root')

        response = dispatch(root_resource, method='POST')
        self.assertEqual(response.status_code, 405)

    def test_delete_success(self):
        root_resource = mock_resource(name='root')
        root_resource.allowed_methods.add('DELETE')

        dispatch(root_resource, method='DELETE')
        self.assertTrue(root_resource.delete.called)

    def test_delete_not_supported(self):
        root_resource = mock_resource(name='root')

        response = dispatch(root_resource, method='DELETE')
        self.assertEqual(response.status_code, 405)

    def test_child_resolution(self):
        child_resource = mock_resource(name='child')
        child_resource.allowed_methods.add('GET')
        child_resource.get = Mock(return_value={})

        root_resource = mock_resource(name='root', child_resource=child_resource)

        dispatch(root_resource, method='GET', resource_path='child')

        root_resource.get_child_resource.assert_called_with('child')
        self.assertTrue(child_resource.get.called)

    def test_grandchild_resolution(self):
        grand_child_resource = mock_resource(name='grandchild')
        grand_child_resource.allowed_methods.add('GET')
        grand_child_resource.get = Mock(return_value={})

        child_resource = mock_resource(name='child', child_resource=grand_child_resource)

        root_resource = mock_resource(name='root', child_resource=child_resource)

        dispatch(root_resource, method='GET', resource_path='child/grandchild')

        root_resource.get_child_resource.assert_called_with('child')
        child_resource.get_child_resource.assert_called_with('grandchild')
        self.assertTrue(grand_child_resource.get.called)

    def test_child_resolution_fail(self):
        root_resource = mock_resource(name='root')

        response = dispatch(root_resource, method='GET', resource_path='child/grandchild')
        self.assertEqual(response.status_code, 404)
