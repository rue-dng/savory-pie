from mock import Mock, patch
import unittest

from savory_pie.django.resources import ModelResource
from savory_pie.fields import AttributeField, IterableField, URIListResourceField
from savory_pie.tests.mock_context import mock_context
from savory_pie.tests.django import mock_orm


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


class URILinksResourceFieldTestCase(unittest.TestCase):

    def test_incoming_with_add(self):
        class MockResource(ModelResource):
            key = Mock()
            model_class = mock_orm.Model
            fields = [
                AttributeField(attribute='bar', type=int),
            ]

        field = URIListResourceField(attribute='foos', resource_class=MockResource)

        source_dict = {
            'foos': ['uri://resources/1', 'uri://resources/2']
        }

        target_object = mock_orm.Mock()
        related_manager = mock_orm.Manager()
        related_manager.all = Mock(return_value=mock_orm.QuerySet())
        target_object.foos = related_manager

        ctx = mock_context()
        foo1_model = Mock()
        foo2_model = Mock()
        mock_resources = Mock()
        resource1 = MockResource(foo1_model)
        resource1.key = 1
        resource2 = MockResource(foo2_model)
        resource2.key = 2
        mock_resources.side_effect = [resource1, resource2]

        ctx.resolve_resource_uri = mock_resources

        field.handle_incoming(ctx, source_dict, target_object)
        related_manager.add.assert_called_with(foo1_model, foo2_model)

    def test_incoming_with_delete(self):
        class MockResource(ModelResource):
            key = Mock()
            model_class = mock_orm.Model
            fields = [
                AttributeField(attribute='bar', type=int),
            ]

        field = URIListResourceField(attribute='foos', resource_class=MockResource)

        source_dict = {
            'foos': ['uri://resources/1', 'uri://resources/2']
        }

        target_object = mock_orm.Mock()
        related_manager = mock_orm.Manager()
        related_manager.remove = Mock()
        related_model1 = mock_orm.Model(pk=1, bar=11)
        related_model2 = mock_orm.Model(pk=2, bar=12)
        related_model3 = mock_orm.Model(pk=3, bar=13)
        mock_resource1 = MockResource(related_model1)
        mock_resource1.key = 1
        mock_resource2 = MockResource(related_model2)
        mock_resource2.key = 2
        mock_resource3 = MockResource(related_model3)
        mock_resource3.key = 3

        field._resource_class = Mock()
        field._resource_class.side_effect = [mock_resource1, mock_resource2, mock_resource3]
        related_manager.all = Mock(return_value=mock_orm.QuerySet(
            related_model1, related_model2, related_model3
        ))
        target_object.foos = related_manager

        ctx = mock_context()
        mock_resources = Mock()
        mock_resources.side_effect = [mock_resource1, mock_resource2]

        ctx.resolve_resource_uri = mock_resources

        field.handle_incoming(ctx, source_dict, target_object)
        related_manager.remove.assert_called_with(related_model3)

    def test_incoming_with_no_change(self):
        class MockResource(ModelResource):
            key = Mock()
            model_class = mock_orm.Model
            fields = [
                AttributeField(attribute='bar', type=int),
                ]

        field = URIListResourceField(attribute='foos', resource_class=MockResource)

        source_dict = {
            'foos': ['uri://resources/1', 'uri://resources/2']
        }

        target_object = mock_orm.Mock()
        related_manager = mock_orm.Manager()
        related_manager.remove = Mock()
        related_model1 = mock_orm.Model(pk=1, bar=11)
        related_model2 = mock_orm.Model(pk=2, bar=12)
        mock_resource1 = MockResource(related_model1)
        mock_resource1.key = 1
        mock_resource2 = MockResource(related_model2)
        mock_resource2.key = 2

        field._resource_class = Mock()
        field._resource_class.side_effect = [mock_resource1, mock_resource2]
        related_manager.all = Mock(return_value=mock_orm.QuerySet(
            related_model1, related_model2
        ))
        target_object.foos = related_manager

        ctx = mock_context()
        mock_resources = Mock()
        mock_resources.side_effect = [mock_resource1, mock_resource2]

        ctx.resolve_resource_uri = mock_resources

        field.handle_incoming(ctx, source_dict, target_object)

        related_manager.remove.assert_called_with()
        related_manager.add.assert_called_with()

    def test_outgoing(self):
        class MockResource(ModelResource):
            model_class = mock_orm.Model
            fields = [
                AttributeField(attribute='bar', type=int),
            ]

        field = URIListResourceField(attribute='foos', resource_class=MockResource)

        source_object = mock_orm.Model()
        related_manager = mock_orm.Manager()
        related_manager.all = Mock(return_value=mock_orm.QuerySet(
            mock_orm.Model(pk=1, bar=14),
            mock_orm.Model(pk=2, bar=14)
        ))

        source_object.foos = related_manager

        ctx = mock_context()
        ctx.build_resource_uri = Mock()
        ctx.build_resource_uri.side_effect = ['uri://resources/1', 'uri://resources/2']

        target_dict = {}
        field.handle_outgoing(ctx, source_object, target_dict)

        self.assertEqual(['uri://resources/1', 'uri://resources/2'], target_dict['foos'])
        