import unittest
import mock_orm
from savory_pie import resources, fields


class User(mock_orm.Model):
    pass


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
        resource = UserQuerySetResource(mock_orm.QuerySet(
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

    def test_get_child_resource_success(self):
        alice = User(pk=1, name='Alice', age=31)
        bob = User(pk=2, name='Bob', age=20)

        queryset_resource = UserQuerySetResource(mock_orm.QuerySet(
            alice,
            bob
        ))

        model_resource = queryset_resource.get_child_resource(1)
        self.assertEqual(model_resource.model, alice)

    def test_get_child_resource_fail(self):
        queryset_resource = QuerySetResource(mock_orm.QuerySet(
            User(pk=1, name='Alice', age=31),
            User(pk=2, name='Bob', age=20)
        ))

        model_resource = query_resource.get_child_resource(999)
        self.assertIsNone(model_resource)