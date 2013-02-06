import unittest
from mock import Mock

from savory_pie.fields import PropertyField

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