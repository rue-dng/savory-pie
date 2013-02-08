import unittest
from mock import Mock

from savory_pie.fields import PropertyField, FKPropertyField


class PropertyFieldTest(unittest.TestCase):
    def test_simple_outgoing(self):
        source_object = Mock()
        source_object.foo = 20

        field = PropertyField(property='foo', type=int)

        target_dict = dict()

        field.handle_outgoing(source_object, target_dict)

        self.assertEqual(target_dict['foo'], 20)

    def test_simple_incoming(self):
        source_dict = {
            'foo': 20
        }

        field = PropertyField(property='foo', type=int)

        target_object = Mock()

        field.handle_incoming(source_dict, target_object)

        self.assertEqual(target_object.foo, 20)

    # TODO: test alternate names


class FKPropertyFieldTest(unittest.TestCase):
    def test_simple_outgoing(self):
        source_object = Mock()
        source_object.foo.bar = 20

        field = FKPropertyField(property='foo.bar', type=int)

        target_dict = dict()

        field.handle_outgoing(source_object, target_dict)

        self.assertEqual(target_dict['bar'], 20)

    def test_simple_incoming(self):
        source_dict = {
            'bar': 20
        }

        field = FKPropertyField(property='foo.bar', type=int)

        target_object = Mock()

        field.handle_incoming(source_dict, target_object)

        self.assertEqual(target_object.foo.bar, 20)

    def test_prepare(self):
        query_set = Mock()

        field = FKPropertyField(property='foo.bar.baz', type=int)

        result_query_set = field.prepare(query_set)

        query_set.select_related.assert_called_with('foo__bar')
        query_set_1 = query_set.select_related.return_value

        self.assertEqual(query_set_1, result_query_set)

    # TODO: test alternate names
