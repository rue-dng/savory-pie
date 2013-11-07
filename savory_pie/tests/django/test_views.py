import unittest
import json
import mock

from mock import Mock
from savory_pie.errors import AuthorizationError
from savory_pie.tests.django.mock_request import savory_dispatch
from savory_pie.django.views import _ParamsImpl
import savory_pie.django.validators


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

    def test_unauthorized(self):
        root_resource = mock_resource(name='root')
        root_resource.allowed_methods.add('PUT')
        root_resource.put.side_effect = AuthorizationError('foo')

        response = savory_dispatch(root_resource, method='PUT', body='{"foo": "bar"}')
        response_json = json.loads(response.content)

        self.assertIn('validation_errors', response_json)
        self.assertEqual(response_json['validation_errors'], ['Modification of field foo not authorized'])
        self.assertEqual(response.status_code, 403)

    def test_get_success(self):
        root_resource = mock_resource(name='root')
        root_resource.allowed_methods.add('GET')
        root_resource.get = Mock(return_value={'foo': 'bar'})

        response = savory_dispatch(root_resource, method='GET')

        self.assertEqual(response.content, '{"foo": "bar"}')
        self.assertTrue(root_resource.get.called)
        self.assertIsNotNone(root_resource.get.call_args_list[0].request)

    def test_get_success_streaming(self):
        def get(ctx, params):
            ctx.streaming_response = True
            ctx.formatter = Mock()
            ctx.formatter.write_to = lambda *args: None
            return iter([
                '{"foo": ',
                '"bar"',
                '}',
            ])

        root_resource = mock_resource(name='root')
        root_resource.allowed_methods.add('GET')
        root_resource.get = Mock(side_effect=get)

        response = savory_dispatch(root_resource, method='GET')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(''.join(response.streaming_content), '{"foo": "bar"}')
        self.assertTrue(root_resource.get.called)
        self.assertIsNotNone(root_resource.get.call_args_list[0].request)

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
        self.assertIsNotNone(root_resource.put.call_args_list[0].request)

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
        self.assertIsNotNone(root_resource.post.call_args_list[0].request)

    def test_post_with_collision_one(self):
        root_resource = mock_resource(name='root')
        root_resource.allowed_methods.add('POST')

        def side_effect(*args):
            # This could occur if a slightly earlier POST or PUT still had
            # the database locked during a DB transaction.
            from django.db.transaction import TransactionManagementError
            raise TransactionManagementError()
        root_resource.post = Mock(side_effect=side_effect)

        response = savory_dispatch(root_resource, method='POST', body='{}')
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.content, '{"resource": "http://localhost/api/"}')

    @mock.patch('django.db.transaction.enter_transaction_management')
    def test_post_with_collision_two(self, enter):
        def side_effect(*args, **kwargs):
            # This could occur if a slightly earlier POST or PUT still had
            # the database locked during a DB transaction.
            from django.db.transaction import TransactionManagementError
            raise TransactionManagementError()
        enter.side_effect = side_effect

        root_resource = mock_resource(name='root')
        new_resource = mock_resource(name='new', resource_path='foo')
        root_resource.post = Mock(return_value=new_resource)
        root_resource.allowed_methods.add('POST')

        response = savory_dispatch(root_resource, method='POST', body='{}')
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.content, '{"resource": "http://localhost/api/"}')

    def test_post_with_exception(self):
        root_resource = mock_resource(name='root')
        root_resource.allowed_methods.add('POST')

        def side_effect(*args):
            raise Exception('Some kind of server error')
        root_resource.post = Mock(side_effect=side_effect)

        response = savory_dispatch(root_resource, method='POST', body='{}')
        self.assertEqual(response.status_code, 500)
        content = json.loads(response.content)
        self.assertTrue('error' in content)
        self.assertTrue(content['error'].startswith('Traceback (most recent call last):'))
        self.assertTrue('Some kind of server error' in content['error'])

    def test_post_not_supported(self):
        root_resource = mock_resource(name='root')

        response = savory_dispatch(root_resource, method='POST')
        self.assertEqual(response.status_code, 405)

    def test_delete_success(self):
        root_resource = mock_resource(name='root')
        root_resource.allowed_methods.add('DELETE')

        savory_dispatch(root_resource, method='DELETE')
        self.assertTrue(root_resource.delete.called)
        self.assertIsNotNone(root_resource.delete.call_args_list[0].request)

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
        self.assertIsNotNone(child_resource.get.call_args_list[0].request)

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
        self.assertIsNotNone(grand_child_resource.get.call_args_list[0].request)

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

    def test_validation_handling(self):
        root_resource = mock_resource(name='root')
        root_resource.allowed_methods.add('PUT')
        root_resource.put.side_effect = savory_pie.django.validators.ValidationError(
            Mock(),
            {
                'class.field': 'broken',
            }
        )

        response = savory_dispatch(root_resource, method='PUT', body='{}')

        response_json = json.loads(response.content)
        self.assertIn('validation_errors', response_json)
        self.assertEqual(response_json['validation_errors']['class.field'], 'broken')
        self.assertEqual(response.status_code, 400)

    def test_set_header(self):
        """
        Tests the set_header method in the APIContext class
        """
        def get(ctx, params):
            ctx.set_header('foo1', 'bar1')
            return {'foo2': 'bar2'}

        root_resource = mock_resource(name='root')
        root_resource.allowed_methods.add('GET')
        root_resource.get = get

        response = savory_dispatch(root_resource, method='GET')

        self.assertEqual(response['foo1'], 'bar1')
        self.assertEqual(response.content, '{"foo2": "bar2"}')


class DjangoPramsTest(unittest.TestCase):

    def test_get_list(self):
        get = Mock(name='mock')
        get.getlist.return_value = ['bar', 'baz']
        params = _ParamsImpl(get)

        result = params.get_list('foo')

        self.assertEqual(result, ['bar', 'baz'])
        get.getlist.assert_called_with('foo')
