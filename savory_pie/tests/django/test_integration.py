import json
import unittest

from mock import Mock

from savory_pie.resources import APIResource
from savory_pie.django import resources, fields

from savory_pie.tests.django import mock_orm
from savory_pie.tests.django.mock_request import savory_dispatch


class User(mock_orm.Model):
    pass

# Need to mock early, QuerySetResource "rightly" assumes it can call all immediately.
User.objects.all = Mock(return_value=mock_orm.QuerySet(
    User(pk=1, name='Alice', age=31),
    User(pk=2, name='Bob', age=20)
))


class UserResource(resources.ModelResource):
    parent_resource_path = 'users'
    model_class = User

    fields = [
        fields.AttributeField(attribute='name', type=str),
        fields.AttributeField(attribute='age', type=int)
    ]


class UserQuerySetResource(resources.QuerySetResource):
    resource_class = UserResource


api_resource = APIResource()
api_resource.register_class(UserQuerySetResource)


class IntegrationTest(unittest.TestCase):
    def test_get_success(self):
        response = savory_dispatch(api_resource, method='GET', resource_path='users/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content),
            {u'resourceUri': u'http://localhost/api/users/1',
             u'age': 31,
             u'name': 'Alice'}
        )
