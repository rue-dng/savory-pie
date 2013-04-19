from mock import Mock, patch
import unittest

from savory_pie.django.resources import ModelResource
from savory_pie.fields import AttributeField, IterableField, MapAccessField
from savory_pie.tests.mock_context import mock_context


class IterableFieldTestCase(unittest.TestCase):

    def test_handle_outgoing_multi_level(self):

        # TODO: Need to alter savory_pie.fields.IterableField.handle_outgoing to not use manager.all()
        from savory_pie.tests.django import mock_orm

        class MockResource(ModelResource):
            model_class = mock_orm.Model
            fields = [
                AttributeField(attribute='bar', type=int),
            ]

        field = IterableField(attribute='foo.fu', resource_class=MockResource)

        source_object = mock_orm.Model()
        related_manager = mock_orm.Manager()
        related_manager.all = Mock(return_value=mock_orm.QuerySet(
            mock_orm.Model(pk=4, bar=14)
        ))

        class InterimObject(object):
            pass

        source_object.foo = InterimObject()
        source_object.foo.fu = related_manager

        target_dict = {}
        field.handle_outgoing(mock_context(), source_object, target_dict)
        self.assertEqual([{'_id': '4', 'bar': 14}], target_dict['foo.fu'])


class TestMapAccessField(unittest.TestCase):
    
    def test_handle_outgoing(self):
        source_obj = {'foo': 'bar', 'name': 'bob'}
        target_dict = {}
        ctx = Mock(name='ctx')
        ctx.formatter.convert_to_public_property.return_value = 'FOO'
        ctx.formatter.to_api_value.side_effect = lambda t, v: v

        field = MapAccessField('foo', str)
        field.handle_outgoing(ctx, source_obj, target_dict)

        self.assertEqual(
            {'FOO': 'bar'},
            target_dict
        )

        ctx.formatter.convert_to_public_property.assert_called_with('foo')
        ctx.formatter.to_api_value.assert_called_with(str, 'bar')
