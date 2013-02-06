import unittest
from mock import Mock

from savory_pie import resources, fields

class UserResource(resources.ModelResource):
    fields = [
        fields.PropertyField(property='name', type=str),
        fields.PropertyField(property='age', type=int)
    ]

class ModelResourceTest(unittest.TestCase):
    def test_get(self):
        user = Mock()
        user.name = 'Bob'
        user.age = 20

        resource = UserResource(user)
        dict = resource.get()

        self.assertEqual(dict['name'], 'Bob')
        self.assertEqual(dict['age'], 20)