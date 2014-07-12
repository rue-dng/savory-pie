import unittest
from mock import Mock, patch

from savory_pie import helpers
from savory_pie.errors import MethodNotAllowedError, PreConditionError


class ResourceHelperTestCase(unittest.TestCase):
    def test_get_not_allowed(self):
        with self.assertRaises(MethodNotAllowedError):
            resource = Mock(name='resource', allowed_methods=['POST'])
            helpers.process_get_request(Mock(name='ctx'), resource, {})

    @patch('savory_pie.helpers._ParamsImpl')
    def test_get(self, ParamsImplClass):
        ParamsImplClass.return_value = 'getparams'
        resource = Mock(name='resource', allowed_methods=['GET'])
        ctx = Mock(name='ctx')
        helpers.process_get_request(ctx, resource, {})
        resource.get.assert_called_with(ctx, 'getparams')

    def test_put_not_allowed(self):
        with self.assertRaises(MethodNotAllowedError):
            resource = Mock(name='resource', allowed_methods=['POST'])
            helpers.process_put_request(Mock(name='ctx'), resource, {})

    @patch('savory_pie.helpers.EmptyParams')
    def test_put_precondition(self, EmptyParamsClass):
        EmptyParamsClass.return_value = 'params'
        with self.assertRaises(PreConditionError):
            resource = Mock(name='resource', allowed_methods=['PUT'])
            resource.get.return_value = {}
            ctx = Mock(name='ctx')
            helpers.process_put_request(ctx, resource, {'data': 'data'}, expected_hash='123')
        resource.put.assert_called_with(ctx, {'data': 'data'})
        resource.get.assert_called_with(ctx, 'params')

    def test_put(self):
        resource = Mock(name='resource', allowed_methods=['PUT'])
        resource.get.return_value = {}
        resource.put.return_value = 'some value'
        ctx = Mock(name='ctx')
        result = helpers.process_put_request(ctx, resource, {'data': 'data'})
        resource.put.assert_called_with(ctx, {'data': 'data'})
        self.assertEqual(result, 'some value')

    def test_post_not_allowed(self):
        with self.assertRaises(MethodNotAllowedError):
            resource = Mock(name='resource', allowed_methods=['GET'])
            helpers.process_post_request(Mock(name='ctx'), resource, {})

    @patch('savory_pie.helpers._ParamsImpl')
    def test_post(self, ParamsImplClass):
        ParamsImplClass.return_value = 'getparams'
        resource = Mock(name='resource', allowed_methods=['POST'])
        ctx = Mock(name='ctx')
        helpers.process_post_request(ctx, resource, {'data': 'data'})
        resource.post.assert_called_with(ctx, {'data': 'data'})

    def test_delete_not_allowed(self):
        with self.assertRaises(MethodNotAllowedError):
            resource = Mock(name='resource', allowed_methods=['GET'])
            helpers.process_delete_request(Mock(name='ctx'), resource)

    @patch('savory_pie.helpers._ParamsImpl')
    def test_delete(self, ParamsImplClass):
        ParamsImplClass.return_value = 'getparams'
        resource = Mock(name='resource', allowed_methods=['DELETE'])
        ctx = Mock(name='ctx')
        helpers.process_delete_request(ctx, resource)
        resource.delete.assert_called_with(ctx)
