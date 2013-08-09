import unittest
from mock import Mock
from savory_pie.auth import authorization, authorization_adapter
from savory_pie.errors import AuthorizationError


class AuthorizationAdapterTestCase(unittest.TestCase):

    def test_adapter(self):
        field = Mock(spec=['to_python_value', '_get', '_compute_property', 'to_api_value'], name='field')
        field._compute_property.return_value = 'source_key'
        field.to_python_value.return_value = 'source'
        source_dict = {'source_key': 'value-source'}
        field._get.return_value = 'target'
        field.to_api_value.return_value = 'target'

        args_name, args_source, args_target = authorization_adapter(field, 'ctx', source_dict, 'target_obj')

        field.to_python_value.called_with('value-source')

        self.assertEqual('source', args_source)
        self.assertEqual('target', args_target)
        self.assertEqual('source_key', args_name)


class AuthorizationDecoratorTestCase(unittest.TestCase):

    def test_no_permission(self):
        def adapter(*args):
            self.assertEqual((field, 'ctx', 'source_dict', 'target_object'), args)
            return 'field', 'source', 'target'

        function = Mock()
        auth = authorization(adapter)
        field = Mock(name='field', spec=['permission'])
        field.permission = None
        value = auth(function)
        value(field, 'ctx', 'source_dict', 'target_object')
        function.assert_called_with(field, 'ctx', 'source_dict', 'target_object')

    def test_authorized(self):
        def adapter(*args):
            self.assertEqual((field, 'ctx', 'source_dict', 'target_object'), args)
            return 'field', 'source', 'target'

        function = Mock()
        auth = authorization(adapter)
        field = Mock(name='field', spec=['permission'])
        field.permission.auth_adapter = None
        field.permission.is_write_authorized.return_value = True
        value = auth(function)
        value(field, 'ctx', 'source_dict', 'target_object')
        field.permission.is_write_authorized.assert_called_with('ctx', 'target_object', 'source', 'target')
        function.assert_called_with(field, 'ctx', 'source_dict', 'target_object')

    def test_not_authorized(self):
        def adapter(*args):
            self.assertEqual((field, 'ctx', 'source_dict', 'target_object'), args)
            return 'field', 'source', 'target'

        function = Mock()

        # Raise an exception if it is called.
        function.side_effect = Exception
        auth = authorization(adapter)
        field = Mock(name='field', spec=['permission'])
        field.permission.auth_adapter = None
        field.permission.is_write_authorized.return_value = False
        value = auth(function)

        with self.assertRaises(AuthorizationError):
            value(field, 'ctx', 'source_dict', 'target_object')
            field.permission.is_write_authorized.assert_called_with('ctx', 'target_object', 'source', 'target')
