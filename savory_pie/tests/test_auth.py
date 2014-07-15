import unittest
from mock import Mock
from savory_pie.auth import authorization, authorization_adapter, datetime_auth_adapter, subobject_auth_adapter
from savory_pie.errors import AuthorizationError


class AuthorizationAdapterTestCase(unittest.TestCase):

    def test_adapter(self):
        field = Mock(spec=['to_python_value', '_get', '_compute_property'], name='field')
        field._compute_property.return_value = 'source_key'
        field.to_python_value.side_effect = ['source', 'target']
        source_dict = {'source_key': 'value-source'}
        field._get.return_value = 'target'

        args_name, args_source, args_target = authorization_adapter(field, 'ctx', source_dict, 'target_obj')

        field.to_python_value.called_with('value-source')

        self.assertEqual('source', args_source)
        self.assertEqual('target', args_target)
        self.assertEqual('source_key', args_name)

    def test_authorization_adapter(self):
        field = Mock(spec=['to_python_value', '_get', '_compute_property'], name='field')
        field._compute_property.return_value = 'source_key'
        field.to_python_value.return_value = 'source'
        field._get.return_value = 'target'

        source_dict = {'source_key': 'value-source'}

        name, source, target = datetime_auth_adapter(field, 'ctx', source_dict, 'targetObj')

        field._get.assert_called_with('targetObj')
        field.to_python_value.assert_called_with('ctx', 'value-source')
        self.assertEqual(name, 'source_key')
        self.assertEqual(source, 'source')
        self.assertEqual(target, 'target')

    def test_subobject_auth_adapter_subobject(self):
        field = Mock(spec=['_resource_class', '_compute_property', 'name'], name='fieldName')
        field.name = 'fieldName'
        field._resource_class.return_value = 'FieldResource'
        field._compute_property.return_value = 'source_name'
        source_dict = {'source_name': {'resourceUri': 'uri'}}
        ctx = Mock(spec=['build_resource_uri'])
        ctx.build_resource_uri.return_value = 'target'
        target_obj = Mock(spec=['fieldName'], fieldName='subObject')

        name, source, target = subobject_auth_adapter(field, ctx, source_dict, target_obj)

        ctx.build_resource_uri.assert_called_with('FieldResource')
        field._resource_class.assert_called_with('subObject')
        self.assertEqual(name, 'source_name')
        self.assertEqual(source, 'uri')
        self.assertEqual(target, 'target')


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
