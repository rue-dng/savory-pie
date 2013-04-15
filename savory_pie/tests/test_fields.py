from mock import Mock, patch
import unittest

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
        