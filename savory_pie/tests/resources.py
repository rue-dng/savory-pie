import unittest
from mock import Mock

from savory_pie import resources, fields


class QuerySet(object):
    def __init__(self, *elements):
        super(QuerySet, self).__init__()
        self.elements = elements

    def __iter__(self):
        return iter(self.elements)

    def filter(self, **kwargs):
        filtered_elements = self.elements
        for key, value in kwargs.iteritems():
            filtered_elements = self._filter(key, value)
        return QuerySet(*filtered_elements)

    def _filter(self, attr, value):
        return [element for element in self.elements if getattr(element, attr) == value]


class Manager(Mock):
    def __init__(self):
        super(Manager, self).__init__()

        self.all = Mock()
        self.all.return_value = QuerySet()


class User(Mock):
    objects = Manager()

    def __init__(self, **kwargs):
        super(User, self).__init__()

        for key, value in kwargs.iteritems():
            setattr(self, key, value)

        self.save = Mock()
        self.delete = Mock()


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
        user = User()

        resource = UserResource(user)
        resource.put({
            'name': 'Bob',
            'age': 20
        })

        self.assertEqual(user.name, 'Bob')
        self.assertEqual(user.age, 20)
        self.assertTrue(user.save.called)

    def test_delete(self):
        user = User()

        resource = UserResource(user)
        resource.delete()

        self.assertTrue(user.delete.called)


class UserQuerySetResource(resources.QuerySetResource):
    resource_class = UserResource
    model_class = User


class QuerySetResourceTest(unittest.TestCase):
    def test_get(self):
        resource = UserQuerySetResource(QuerySet(
            User(name='Alice', age=31),
            User(name='Bob', age=20)
        ))
        data = resource.get()

        self.assertEqual(data['objects'], [
            {'name': 'Alice', 'age': 31},
            {'name': 'Bob', 'age': 20}
        ])

    def test_post(self):
        queryset_resource = UserQuerySetResource()

        new_resource = queryset_resource.post({
            'name': 'Bob',
            'age': 20
        })

        new_user = new_resource.model

        self.assertEqual(new_user.name, 'Bob')
        self.assertEqual(new_user.age, 20)
        self.assertTrue(new_user.save.called)

    def test_child_resource(self):
        queryset_resource = UserQuerySetResource(QuerySet(
            User(pk=1, name='Alice', age=31),
            User(pk=2, name='Bob', age=20)
        ))

        queryset_resource.get_child_resource(20)