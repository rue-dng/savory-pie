import unittest

import mock
from mock import MagicMock, Mock

from savory_pie.django.validators import ValidationError
from savory_pie.django.resources import ModelResource
from savory_pie.fields import AttributeField, IterableField, SubObjectResourceField, CompleteURIResourceField
from savory_pie.tests.mock_context import mock_context


class IterableFieldTest(unittest.TestCase):

    def test_handle_outgoing_multi_level(self):

        # TODO: Need to alter savory_pie.fields.IterableField.handle_outgoing to not use manager.all()
        from savory_pie.tests.django import mock_orm

        class ORMModelMock(mock_orm.Model):
            pass

        class MockResource(ModelResource):
            model_class = mock_orm.Model
            fields = [
                AttributeField(attribute='bar', type=int),
            ]

        field = IterableField(attribute='foo.fu', resource_class=MockResource)

        source_object = mock_orm.Model()
        related_manager = mock_orm.Manager()
        related_manager.all = Mock(return_value=mock_orm.QuerySet(
            ORMModelMock(pk=4, bar=14)
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
            model_class = Mock()
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

    def test_incoming_push_pop(self):
        Resource = Mock(name='resource')
        ctx = mock_context()

        field = IterableField(attribute='foo', resource_class=Resource)

        source_dict = {
            'foo': {'bar': 20},
        }

        target_object = MagicMock()
        target_object.__iter__ = iter([])
        field.handle_incoming(ctx, source_dict, target_object)

        ctx.assert_has_calls([
            mock.call.push(target_object),
            mock.call.pop(),
        ])


class IterableFieldTestCase(unittest.TestCase):
    def test_handle_incoming_pre_save_optional(self):
        ctx = mock_context()
        ctx.resolve_resource_uri = Mock(name='resolve_resource_uri')
        sub_resource = ctx.resolve_resource_uri.return_value
        Resource = Mock(name='resource')

        source_dict = {
            'foo': {
                'resourceUri': 'foo'
            },
        }
        target_obj = Mock(['save', 'pre_save'], name='target_obj',)
        field = SubObjectResourceField('foo', Resource)

        field.handle_incoming(ctx, source_dict, target_obj)

        self.assertEqual(sub_resource.model, target_obj.foo)

    def test_incoming_push_pop(self):
        Resource = Mock(name='resource')
        ctx = mock_context()

        field = SubObjectResourceField(attribute='foo', resource_class=Resource)

        source_dict = {
            'foo': {'bar': 20},
        }

        target_object = Mock()
        field.handle_incoming(ctx, source_dict, target_object)

        ctx.assert_has_calls([
            mock.call.push(target_object),
            mock.call.pop(),
        ])


class CompleteURIResourceFieldTestCase(unittest.TestCase):
    def test_outgoing(self):

        class Resource(ModelResource):
            model_class = Mock()
            parent_resource_path = 'resources'

        field = CompleteURIResourceField(resource_class=Resource)

        source_object = Mock()
        ctx = mock_context()
        ctx.build_resource_uri = Mock()
        ctx.build_resource_uri.side_effect = ['uri://resources/1']

        target_dict = dict()
        field.handle_outgoing(ctx, source_object, target_dict)

        self.assertEqual(target_dict['completeResourceUri'], 'uri://resources/1')


class AttributeFieldTestCase(unittest.TestCase):
    def test_incoming_required_and_present(self):
        ctx = mock_context()
        source_dict = {
            'foo': 20
        }

        class TargetObject:
            foo = 0
        target_object = TargetObject()
        field = AttributeField('foo', type=int)

        field.handle_incoming(ctx, source_dict, target_object)
        self.assertEqual(target_object.foo, 20)

    def test_incoming_required_and_missing(self):
        ctx = mock_context()
        source_dict = {
            'foo': 20
        }

        class TargetObject:
            foo = 0
        target_object = TargetObject()
        field = AttributeField('bar', type=int)

        with self.assertRaises(ValidationError):
            field.handle_incoming(ctx, source_dict, target_object)
        self.assertEqual(target_object.foo, 0)

    def test_incoming_optional_and_present(self):
        ctx = mock_context()
        source_dict = {
            'foo': 20
        }

        class TargetObject:
            foo = 0
        target_object = TargetObject()
        field = AttributeField('foo', type=int, optional=True)

        field.handle_incoming(ctx, source_dict, target_object)
        self.assertEqual(target_object.foo, 20)

    def test_incoming_optional_and_missing(self):
        ctx = mock_context()
        source_dict = {
            'foo': 20
        }

        class TargetObject:
            foo = 0
        target_object = TargetObject()
        field = AttributeField('bar', type=int, optional=True)

        field.handle_incoming(ctx, source_dict, target_object)
        self.assertEqual(target_object.foo, 0)
