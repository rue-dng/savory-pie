import unittest
from StringIO import StringIO

from mock import Mock
from savory_pie import views

class Request(object):
    def __init__(self, method, path, body=None, GET=None, POST=None):
        self.method = method
        self.body = body
        self.body_file = None

        self.GET = GET or {}
        self.POST = POST or {}
        self.REQUEST = dict(self.GET, **self.POST)

    def read(self):
        if not self.body_file:
            self.body_file = StringIO(self.body)

        return self.body_file.read()


class ViewTest(unittest.TestCase):
    def test_get_success(self):
        resource = Mock()
        resource.get = Mock(return_value={})

        view = views.service_dispatcher(resource)
        view(Request(method='GET', path='/'))

        self.assertTrue(resource.get.called)

    def test_get_not_supported(self):
        resource = object()

        view = views.service_dispatcher(resource)
        response = view(Request(method='GET', path='/'))

        self.assertEqual(response.status_code, 405)

    def test_put_success(self):
        root_resource = Mock()
        new_resource = Mock()

        root_resource.put = Mock(return_value=new_resource)

        view = views.service_dispatcher(root_resource)
        view(Request(method='PUT', path='/', body='{}'))

        root_resource.put.assert_called_with({})

    def test_put_not_supported(self):
        resource = object()

        view = views.service_dispatcher(resource)
        response = view(Request(method='PUT', path='/'))

        self.assertEqual(response.status_code, 405)

    def test_post_success(self):
        root_resource = Mock()
        root_resource.post = Mock()

        view = views.service_dispatcher(root_resource)
        view(Request(method='POST', path='/', body='{}'))

        root_resource.post.assert_called_with({})

    def test_post_not_supported(self):
        resource = object()

        view = views.service_dispatcher(resource)
        response = view(Request(method='POST', path='/'))

        self.assertEqual(response.status_code, 405)

    def test_delete(self):
        root_resource = Mock()
        root_resource.delete = Mock()

        view = views.service_dispatcher(root_resource)
        view(Request(method='DELETE', path='/'))

        self.assertTrue(root_resource.delete.called)

    def test_delete_not_supported(self):
        resource = object()

        view = views.service_dispatcher(resource)
        response = view(Request(method='DELETE', path='/'))

        self.assertEqual(response.status_code, 405)