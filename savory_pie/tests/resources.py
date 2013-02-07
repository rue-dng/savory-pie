import unittest
from mock import Mock

from savory_pie import resources, fields

class User(Mock):
    objects = Mock()

    def __init__(self, **kwargs):
        super(User, self).__init__()

        for key, value in kwargs.iteritems():
            setattr(self, key, value)


class UserResource(resources.ModelResource):
    fields = [
        fields.PropertyField(property='name', type=str),
        fields.PropertyField(property='age', type=int)
    ]


class ModelResourceTest(unittest.TestCase):
    def test_get(self):
        user = User(name='Bob', age=20)

        resource = UserResource(user)
        dict = resource.get()

        self.assertEqual(dict['name'], 'Bob')
        self.assertEqual(dict['age'], 20)

    def test_put(self):
        user = Mock()
        user.save = Mock()

        resource = UserResource(user)
        resource.put({
            'name': 'Bob',
            'age': 20
        })

        self.assertEqual(user.name, 'Bob')
        self.assertEqual(user.age, 20)
        self.assertTrue(user.save.called)

    def test_delete(self):
        user = Mock()
        user.delete = Mock()

        resource = UserResource(user)
        resource.delete()

        self.assertTrue(user.delete.called)


class UserQuerySetResource(resources.QuerySetResource):
    resource_class = UserResource
    model_class = User

class QuerySetResourceTest(unittest.TestCase):
    User.objects.all.return_value = [
        User
    ]
