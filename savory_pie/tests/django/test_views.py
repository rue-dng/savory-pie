import unittest
import json

from mock import Mock
from savory_pie.tests.django.mock_request import savory_dispatch


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


def call_args_sans_context(mock):
    return list(mock.call_args[0][1:])


class ViewTest(unittest.TestCase):
    def test_get_success(self):
        root_resource = mock_resource(name='root')
        root_resource.allowed_methods.add('GET')
        root_resource.get = Mock(return_value={'foo': 'bar'})

        response = savory_dispatch(root_resource, method='GET')
        self.assertEqual(response.content, '{"foo": "bar"}')

        self.assertTrue(root_resource.get.called)

    def test_get_not_supported(self):
        root_resource = mock_resource(name='root')

        response = savory_dispatch(root_resource, method='GET')
        self.assertEqual(response.status_code, 405)

    def test_put_success(self):
        root_resource = mock_resource(name='root')
        root_resource.allowed_methods.add('PUT')

        response = savory_dispatch(root_resource, method='PUT', body='{"foo": "bar"}')

        self.assertTrue(call_args_sans_context(root_resource.put), [{
            'foo': 'bar'
        }])
        self.assertEqual(response.status_code, 204)

    def test_put_not_supported(self):
        root_resource = mock_resource(name='root')

        response = savory_dispatch(root_resource, method='PUT')
        self.assertEqual(response.status_code, 405)

    def test_post_success(self):
        root_resource = mock_resource(name='root')
        root_resource.allowed_methods.add('POST')

        new_resource = mock_resource(name='new', resource_path='foo')
        root_resource.post = Mock(return_value=new_resource)

        response = savory_dispatch(root_resource, method='POST', body='{}')

        self.assertTrue(call_args_sans_context(root_resource.post), [{
             'foo': 'bar'
        }])
        self.assertEqual(response['Location'], 'http://localhost/api/foo')

    def test_post_not_supported(self):
        root_resource = mock_resource(name='root')

        response = savory_dispatch(root_resource, method='POST')
        self.assertEqual(response.status_code, 405)

    def test_delete_success(self):
        root_resource = mock_resource(name='root')
        root_resource.allowed_methods.add('DELETE')

        savory_dispatch(root_resource, method='DELETE')
        self.assertTrue(root_resource.delete.called)

    def test_delete_not_supported(self):
        root_resource = mock_resource(name='root')

        response = savory_dispatch(root_resource, method='DELETE')
        self.assertEqual(response.status_code, 405)

    def test_child_resolution(self):
        child_resource = mock_resource(name='child')
        child_resource.allowed_methods.add('GET')
        child_resource.get = Mock(return_value={})

        root_resource = mock_resource(name='root', child_resource=child_resource)

        savory_dispatch(root_resource, method='GET', resource_path='child')

        self.assertEqual(call_args_sans_context(root_resource.get_child_resource), ['child'])
        self.assertTrue(child_resource.get.called)

    def test_grandchild_resolution(self):
        grand_child_resource = mock_resource(name='grandchild')
        grand_child_resource.allowed_methods.add('GET')
        grand_child_resource.get = Mock(return_value={})

        child_resource = mock_resource(name='child', child_resource=grand_child_resource)

        root_resource = mock_resource(name='root', child_resource=child_resource)

        savory_dispatch(root_resource, method='GET', resource_path='child/grandchild')

        self.assertEqual(call_args_sans_context(root_resource.get_child_resource), ['child'])
        self.assertEqual(call_args_sans_context(child_resource.get_child_resource), ['grandchild'])
        self.assertTrue(grand_child_resource.get.called)

    def test_child_resolution_fail(self):
        root_resource = mock_resource(name='root')

        response = savory_dispatch(root_resource, method='GET', resource_path='child/grandchild')
        self.assertEqual(response.status_code, 404)

    def test_exception_handling(self):
        root_resource = mock_resource(name='root')
        root_resource.allowed_methods.add('GET')
        root_resource.get.side_effect = Exception('Fail')

        response = savory_dispatch(root_resource, method='GET')

        response_json = json.loads(response.content)
        self.assertIn('error', response_json)
        self.assertEqual(response.status_code, 500)
