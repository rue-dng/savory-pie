from mock import Mock
import unittest

from savory_pie.fields import AttributeField, IterableField
from savory_pie.resources import Resource
from savory_pie.tests.mock_context import mock_context

class IterableFieldTestCase(unittest.TestCase):
    class SingleLevelResource(Resource):
        parent_resource_path = 'resources'

    class MultiLevelResource(Resource):
        parent_resource_path = 'resources/subresource'
        resource_path = 'subresource'

    def setUp(self):
        # Set up ctx
        self.ctx = mock_context()
        # Set up source_dict

    # def test_simple_outgoing(self):
    #     source_object = Mock()
    #     source_object.foo = 20
    #
    #     target_dict = dict()
    #
    #     field = AttributeField(attribute='foo', type=int)
    #     field.handle_outgoing(mock_context(), source_object, target_dict)
    #
    #     self.assertEqual(target_dict['foo'], 20)
    #
    # def test_simple_none_outgoing(self):
    #     source_object = Mock()
    #     source_object.foo = None
    #
    #     target_dict = dict()
    #
    #     field = AttributeField(attribute='foo', type=int)
    #     field.handle_outgoing(mock_context(), source_object, target_dict)
    #
    #     self.assertEqual(target_dict['foo'], None)
    #
    # def test_multilevel_outgoing(self):
    #     source_object = Mock()
    #     source_object.foo.bar = 20
    #
    #     field = AttributeField(attribute='foo.bar', type=int)
    #
    #     target_dict = dict()
    #
    #     field.handle_outgoing(mock_context(), source_object, target_dict)
    #
    #     self.assertEqual(target_dict['bar'], 20)


#This test clearly doesn't work...

    #def test_outgoing(self):
#
#        class GenericModel(object):
#            pass
#
#        class MockResource(Resource):
#            model_class = GenericModel
#            fields = [
#                AttributeField(attribute='bar', type=int),
#            ]
#
#        # field = RelatedManagerField(attribute='foo', resource_class=MockResource)
#        field = IterableField(attribute='foo', resource_class=GenericModel)
#
#        source_object = GenericModel()
#        source_object.foo = 'blah'
#        target_dict = {}
#        field.handle_outgoing(mock_context(), source_object, target_dict)
#        # self.assertEqual([{'_id': '4', 'bar': 14}], target_dict['foo'])
