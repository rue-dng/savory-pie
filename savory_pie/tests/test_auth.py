import unittest
from mock import Mock
from savory_pie.auth import UserPermissionValidator, authorization, authorization_adapter
from savory_pie.errors import AuthorizationError


class AuthorizationAdapterTestCase(unittest.TestCase):

    def test_adapter(self):
        field = Mock(spec=['to_python_value', '_get', '_compute_property'], name='field')
        field._compute_property.return_value = 'source_key'
        field.to_python_value.return_value = 'source'
        source_dict = {'source_key': 'value-source'}
        field._get.return_value = 'target'

        args_ctx, args_target_obj, args_source, args_target = authorization_adapter(field, 'ctx', source_dict, 'target_obj')

        field.to_python_value.called_with('value-source')

        self.assertEqual('ctx', args_ctx)
        self.assertEqual('target_obj', args_target_obj)
        self.assertEqual('source', args_source)
        self.assertEqual('target', args_target)


class UserPermissionValidatorTestCase(unittest.TestCase):

    def test_target_source_changed(self):
        validator = UserPermissionValidator('value')
        ctx = Mock(spec=['user'])
        ctx.user.has_perm.return_value = False
        self.assertFalse(validator.is_write_authorized(ctx, None, 'a', 'b'))
        ctx.user.has_perm.assert_called_with('value')

    def test_target_source_not_changed(self):
        validator = UserPermissionValidator('value')
        ctx = Mock(spec=['user'])
        # Should not call has_perm
        ctx.user.has_perm.side_effect = Exception
        self.assertTrue(validator.is_write_authorized(ctx, None, 'a', 'a'))


class AuthorizationDecoratorTestCase(unittest.TestCase):

    def test_no_permission(self):
        def adapter(*args):
            self.assertEqual((field, 'ctx', 'source_dict', 'target_object'), args)
            return ['new_args']

        function = Mock()
        auth = authorization(adapter)
        field = Mock(name='field', spec=['permission'])
        field.permission = None
        value = auth(function)
        value(field, 'ctx', 'source_dict', 'target_object')
        function.assert_called_with('ctx', 'source_dict', 'target_object')

    def test_authorized(self):
        def adapter(*args):
            self.assertEqual((field, 'ctx', 'source_dict', 'target_object'), args)
            return ['new_args']

        function = Mock()
        auth = authorization(adapter)
        field = Mock(name='field', spec=['permission'])
        field.permission.is_write_authorized.return_value = True
        value = auth(function)
        value(field, 'ctx', 'source_dict', 'target_object')
        field.permission.is_write_authorized.assert_called_with('new_args')
        function.assert_called_with('ctx', 'source_dict', 'target_object')

    def test_not_authorized(self):
        def adapter(*args):
            self.assertEqual((field, 'ctx', 'source_dict', 'target_object'), args)
            return ['new_args']

        function = Mock()

        # Raise an exception if it is called.
        function.side_effect = Exception
        auth = authorization(adapter)
        field = Mock(name='field', spec=['permission'])
        field.permission.is_write_authorized.return_value = False
        value = auth(function)

        with self.assertRaises(AuthorizationError):
            value(field, 'ctx', 'source_dict', 'target_object')
            field.permission.is_write_authorized.assert_called_with('new_args')
