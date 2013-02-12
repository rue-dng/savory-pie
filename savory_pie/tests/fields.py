import unittest
from mock import Mock

from savory_pie.resources import ModelResource, QuerySetResource
from savory_pie.fields import PropertyField, FKPropertyField, SubModelResourceField, RelatedManagerField

from savory_pie.tests.mock_requests import mock_get, mock_put, mock_post

class PropertyFieldTest(unittest.TestCase):
    def test_simple_outgoing(self):
        source_object = Mock()
        source_object.foo = 20

        field = PropertyField(property='foo', type=int)

        target_dict = dict()

        field.handle_outgoing(mock_get(), source_object, target_dict)

        self.assertEqual(target_dict['foo'], 20)

    def test_simple_incoming(self):
        source_dict = {
            'foo': 20
        }

        field = PropertyField(property='foo', type=int)

        target_object = Mock()

        field.handle_incoming(mock_put(), source_dict, target_object)

        self.assertEqual(target_object.foo, 20)

    def test_alternate_name_outgoing(self):
        source_object = Mock()
        source_object.foo = 20

        field = PropertyField(property='foo', type=int, json_property='bar')

        target_dict = dict()

        field.handle_outgoing(mock_get(), source_object, target_dict)

        self.assertEqual(target_dict['bar'], 20)

    def test_alternate_name_incoming(self):
        source_dict = {
            'bar': 20
        }

        field = PropertyField(property='foo', type=int, json_property='bar')

        target_object = Mock()

        field.handle_incoming(mock_post(), source_dict, target_object)

        self.assertEqual(target_object.foo, 20)

    def test_automatic_json_naming(self):
        field = PropertyField(property='foo_bar', type=int)

        target_object = Mock()
        field.handle_incoming(mock_put(), {'fooBar': 20}, target_object)

        self.assertEqual(target_object.foo_bar, 20)


class FKPropertyFieldTest(unittest.TestCase):
    def test_simple_outgoing(self):
        source_object = Mock()
        source_object.foo.bar = 20

        field = FKPropertyField(property='foo.bar', type=int)

        target_dict = dict()

        field.handle_outgoing(mock_get(), source_object, target_dict)

        self.assertEqual(target_dict['bar'], 20)

    def test_simple_incoming(self):
        source_dict = {
            'bar': 20
        }

        field = FKPropertyField(property='foo.bar', type=int)

        target_object = Mock()

        field.handle_incoming(mock_post(), source_dict, target_object)

        self.assertEqual(target_object.foo.bar, 20)

    def test_alternate_name_outgoing(self):
        source_object = Mock()
        source_object.foo.bar = 20

        field = FKPropertyField(property='foo.bar', type=int, json_property='foo')

        target_dict = dict()

        field.handle_outgoing(mock_get(), source_object, target_dict)

        self.assertEqual(target_dict['foo'], 20)

    def test_alternate_name_incoming(self):
        source_dict = {
            'foo': 20
        }

        field = FKPropertyField(property='foo.bar', type=int, json_property='foo')

        target_object = Mock()

        field.handle_incoming(mock_post(), source_dict, target_object)

        self.assertEqual(target_object.foo.bar, 20)

    def test_prepare(self):
        query_set = Mock()
        query_set.query.select_related = {}

        field = FKPropertyField(property='foo.bar.baz', type=int)

        result_query_set = field.prepare(query_set)

        self.assertEqual({'foo': {'bar': {}}}, query_set.query.select_related)
        self.assertEqual(query_set, result_query_set)


class SubModelResourceFieldTest(unittest.TestCase):
    def test_simple_outgoing(self):
        source_object = Mock()
        source_object.foo.bar = 20

        class Resource(ModelResource):
            fields = [
                PropertyField(property='bar', type=int),
            ]
        field = SubModelResourceField(property='foo', resource_class=Resource)

        target_dict = dict()

        field.handle_outgoing(mock_get(), source_object, target_dict)

        self.assertEqual(target_dict['foo'], {'bar': 20})

    def test_simple_incoming(self):
        source_dict = {
            'foo': {'bar': 20},
        }

        class Resource(ModelResource):
            model_class = Mock()
            fields = [
                PropertyField(property='bar', type=int),
            ]
        field = SubModelResourceField(property='foo', resource_class=Resource)

        target_object = Mock()

        field.handle_incoming(mock_put(), source_dict, target_object)

        self.assertEqual(20, target_object.foo.bar)
        target_object.foo.save.assert_called_with()

    def test_new_object_incoming(self):
        source_dict = {
            'foo': {'bar': 20},
        }

        class Resource(ModelResource):
            model_class = Mock()
            fields = [
                PropertyField(property='bar', type=int),
            ]
        field = SubModelResourceField(property='foo', resource_class=Resource)

        target_object = Mock()
        target_object.foo = None

        field.handle_incoming(mock_post(), source_dict, target_object)

        self.assertEqual(20, target_object.foo.bar)
        self.assertEqual(Resource.model_class.return_value, target_object.foo)
        target_object.foo.save.assert_called_with()


class RelatedManagerFieldTest(unittest.TestCase):
    def test_outgoing(self):

        class MockResource(ModelResource):
            model_class = Mock()
            fields = [
                PropertyField(property='bar', type=int),
            ]


        class MockQuerySetResource(QuerySetResource):
            resource_class = MockResource

        field = RelatedManagerField(property='foo', resource_class=MockQuerySetResource)

        source_object = Mock()
        source_object.foo.all.return_value.filter.return_value = [Mock(bar=14)]

        target_dict = {}

        field.handle_outgoing(mock_get(), source_object, target_dict)

        self.assertEqual([{'bar': 14}], target_dict['foo'])
