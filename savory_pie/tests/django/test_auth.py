import unittest
from mock import Mock
from savory_pie.django.auth import DjangoUserPermissionValidator


class DjangoUserPermissionValidatorTestCase(unittest.TestCase):

    def test_target_source_changed(self):
        validator = DjangoUserPermissionValidator('value')
        ctx = Mock(spec=['user'])
        ctx.request = Mock()
        ctx.request.user.has_perm.return_value = False
        self.assertFalse(validator.is_write_authorized(ctx, None, 'a', 'b'))
        ctx.request.user.has_perm.assert_called_with('value')

    def test_target_source_not_changed(self):
        validator = DjangoUserPermissionValidator('value')
        ctx = Mock(spec=['user'])
        ctx.request = Mock()
        # Should not call has_perm
        ctx.request.user.has_perm.side_effect = Exception
        self.assertTrue(validator.is_write_authorized(ctx, None, 'a', 'a'))
