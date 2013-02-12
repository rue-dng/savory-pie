import unittest
from StringIO import StringIO

from mock import Mock
from savory_pie import views


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
        return 'http://' + self.host + '/' + self.path

    def read(self):
        if not self.body_file:
            self.body_file = StringIO(self.body)

        return self.body_file.read()


class ViewTest(unittest.TestCase):
    def test_get_success(self):
        root_resource = Mock()
        root_resource.get = Mock(return_value={'foo': 'bar'})

        response = dispatch(root_resource, method='GET')
        self.assertEqual(response.content, '{"foo": "bar"}')

        self.assertTrue(root_resource.get.called)

    def test_get_not_supported(self):
        root_resource = object()

        response = dispatch(root_resource, method='GET')
        self.assertEqual(response.status_code, 405)

    def test_put_success(self):
        root_resource = Mock()
        new_resource = Mock()

        root_resource.put = Mock(return_value=new_resource)

        dispatch(root_resource, method='PUT', body='{}')

        root_resource.put.assert_called_with({})

    def test_put_not_supported(self):
        root_resource = object()

        response = dispatch(root_resource, method='PUT')
        self.assertEqual(response.status_code, 405)

    def test_post_success(self):
        root_resource = Mock()
        root_resource.post = Mock()

        dispatch(root_resource, method='POST', body='{}')

        root_resource.post.assert_called_with({})

    def test_post_not_supported(self):
        root_resource = object()

        response = dispatch(root_resource, method='POST')
        self.assertEqual(response.status_code, 405)

    def test_delete(self):
        root_resource = Mock()
        root_resource.delete = Mock()

        dispatch(root_resource, method='DELETE')

        self.assertTrue(root_resource.delete.called)

    def test_delete_not_supported(self):
        root_resource = object()

        response = dispatch(root_resource, method='DELETE')
        self.assertEqual(response.status_code, 405)

    def test_child_resolution(self):
        child_resource = Mock(name='child')
        child_resource.get = Mock(return_value={})

        root_resource = Mock(name='root')
        root_resource.get_child_resource = Mock(return_value=child_resource)

        dispatch(root_resource, method='GET', resource_path='child')

        root_resource.get_child_resource.assert_called_with('child')
        self.assertTrue(child_resource.get.called)

    def test_grandchild_resolution(self):
        grand_child_resource = Mock(name='grandchild')
        grand_child_resource.get = Mock(return_value={})

        child_resource = Mock(name='child')
        child_resource.get_child_resource = Mock(return_value=grand_child_resource)

        root_resource = Mock(name='root')
        root_resource.get_child_resource = Mock(return_value=child_resource)

        dispatch(root_resource, method='GET', resource_path='child/grandchild')

        root_resource.get_child_resource.assert_called_with('child')
        child_resource.get_child_resource.assert_called_with('grandchild')
        self.assertTrue(grand_child_resource.get.called)

    def test_child_resolution_fail(self):
        root_resource = Mock(name='root')
        root_resource.get_child_resource = Mock(return_value=None)

        response = dispatch(root_resource, method='GET', resource_path='child/grandchild')
        self.assertEqual(response.status_code, 404)
