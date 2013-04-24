from mock import MagicMock, Mock, patch
import unittest

from savory_pie.resources import Resource
from savory_pie.django.resources import ModelResource
from savory_pie.fields import AttributeField, IterableField
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

    def test_iterable_factory_outgoing(self):
        values = [
            Mock(name='value1', bar=1),
            Mock(name='value2', bar=2),
            Mock(name='value3', bar=3),
        ]
        iterable = MagicMock(name='iterable')
        iterable.__iter__.return_value = iter(values)

        class MockResource(ModelResource):
            fields = [
                AttributeField(attribute='bar', type=int),
            ]

        iterable_factory = Mock(name='iterable_factory', return_value=iterable)

        source_object = Mock(name='source_object')
        target_dict = {}

        field = IterableField(attribute='foo', resource_class=MockResource, iterable_factory=iterable_factory)

        field.handle_outgoing(mock_context(), source_object, target_dict)

        self.assertEqual(
            target_dict['foo'],
            [
                {
                    'bar': 1,
                    '_id': str(values[0].pk),
                },
                {
                    'bar': 2,
                    '_id': str(values[1].pk),
                },
                {
                    'bar': 3,
                    '_id': str(values[2].pk),
                },
            ]
        )

        iterable_factory.assert_called_with(source_object.foo)
