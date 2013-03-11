import unittest
from mock import Mock, MagicMock, call, patch

from savory_pie.django import resources, fields
from savory_pie.tests.django import mock_orm
from savory_pie.tests.mock_context import mock_context

from datetime import datetime

import django.core.exceptions
from django.contrib.auth.models import User as DjangoUser


class ResourceTest(unittest.TestCase):
    def test_no_allowed_methods(self):
        resource = resources.Resource()
        self.assertEqual(resource.allowed_methods, set())

    def test_allows_get(self):
        resource = resources.Resource()
        resource.get = lambda: dict()
        self.assertEqual(resource.allowed_methods, {'GET'})


class User(mock_orm.Model):
    pass


class AddressableUserResource(resources.ModelResource):
    parent_resource_path = 'users'
    model_class = User

    fields = [
        fields.AttributeField(attribute='name', type=str),
        fields.AttributeField(attribute='age', type=int)
    ]


class UnaddressableUserResource(resources.ModelResource):
    model_class = User

    fields = [
        fields.AttributeField(attribute='name', type=str),
        fields.AttributeField(attribute='age', type=int)
    ]


class ComplexUserResource(resources.ModelResource):
    model_class = User

    fields = [
        fields.SubModelResourceField(attribute='manager', resource_class=UnaddressableUserResource),
        fields.RelatedManagerField(attribute='reports', resource_class=UnaddressableUserResource)
    ]

class ModelResourceTest(unittest.TestCase):
    def test_resource_path(self):
        user = User(pk=1, name='Bob', age=20)
        resource = AddressableUserResource(user)

        self.assertEqual(resource.resource_path, 'users/1')

    def test_get(self):
        user = User(pk=1, name='Bob', age=20)

        resource = AddressableUserResource(user)
        dict = resource.get(mock_context())

        self.assertEqual(dict, {
            'name': 'Bob',
            'age': 20,
            'resourceUri': 'uri://users/1'
        })

    def test_put(self):
        user = User()

        resource = AddressableUserResource(user)
        resource.put(mock_context(), {
            'name': 'Bob',
            'age': 20
        })

        self.assertEqual(user.name, 'Bob')
        self.assertEqual(user.age, 20)
        self.assertTrue(user.save.called)

    def test_delete(self):
        user = User()

        resource = AddressableUserResource(user)
        resource.delete(mock_context())

        self.assertTrue(user.delete.called)

    def test_get_by_source_dict(self):
        source_dict = {
            'name': 'Bob',
            'age': 15,
        }

        with patch.object(AddressableUserResource.model_class, 'objects') as objects:
            AddressableUserResource.get_by_source_dict(mock_context(), source_dict)

        objects.filter.assert_called_with(name='Bob', age=15)

    def test_get_by_source_dict_not_found(self):
        source_dict = {
            'name': 'Bob',
            'age': 15,
        }

        with patch.object(AddressableUserResource.model_class, 'objects') as objects:
            objects.filter.get.return_value = django.core.exceptions.ObjectDoesNotExist
            AddressableUserResource.get_by_source_dict(mock_context(), source_dict)

        objects.filter.assert_called_with(name='Bob', age=15)

    def test_get_by_source_dict_filter_by_item_optional(self):
        source_dict = {
            'name': 'Bob',
            'age': 15,
        }

        with patch.object(ComplexUserResource.model_class, 'objects') as objects:
            ComplexUserResource.get_by_source_dict(mock_context(), source_dict)

        objects.filter.assert_called_with()


class AddressableUserQuerySetResource(resources.QuerySetResource):
    resource_path = 'users'
    resource_class = AddressableUserResource


class SemiUnaddressableUserQuerySetResource(resources.QuerySetResource):
    resource_path = 'users'
    resource_class = UnaddressableUserResource


class FullyUnaddressableUserQuerySetResource(resources.QuerySetResource):
    resource_class = UnaddressableUserResource


class ComplexUserResourceQuerySetResource(resources.QuerySetResource):
    resource_class = ComplexUserResource


class QuerySetResourceTest(unittest.TestCase):
    def test_get(self):
        resource = AddressableUserQuerySetResource(mock_orm.QuerySet(
            User(pk=1, name='Alice', age=31),
            User(pk=2, name='Bob', age=20)
        ))
        data = resource.get(mock_context())

        self.assertEqual(data['objects'], [
            {'resourceUri': 'uri://users/1', 'name': 'Alice', 'age': 31},
            {'resourceUri': 'uri://users/2', 'name': 'Bob', 'age': 20}
        ])

    def test_addressable_post(self):
        queryset_resource = AddressableUserQuerySetResource()

        new_resource = queryset_resource.post(mock_context(), {
            'name': 'Bob',
            'age': 20
        })

        new_user = new_resource.model
        self.assertEqual(new_resource.resource_path, 'users/' + str(new_user.pk))

        self.assertEqual(new_user.name, 'Bob')
        self.assertEqual(new_user.age, 20)
        self.assertTrue(new_user.save.called)

    def test_semi_unaddressable_post(self):
        queryset_resource = SemiUnaddressableUserQuerySetResource()

        new_resource = queryset_resource.post(mock_context(), {
            'name': 'Bob',
            'age': 20
        })
        self.assertEqual(new_resource.resource_path, 'users/' + str(new_resource.model.pk))

    def test_fully_unaddressable_post(self):
        queryset_resource = FullyUnaddressableUserQuerySetResource()

        new_resource = queryset_resource.post(mock_context(), {
            'name': 'Bob',
            'age': 20
        })
        self.assertIsNone(new_resource.resource_path)

    def test_get_child_resource_success(self):
        alice = User(pk=1, name='Alice', age=31)
        bob = User(pk=2, name='Bob', age=20)

        queryset_resource = AddressableUserQuerySetResource(mock_orm.QuerySet(
            alice,
            bob
        ))

        model_resource = queryset_resource.get_child_resource(mock_context(), 1)
        self.assertEqual(model_resource.model, alice)

    def test_get_child_resource_fail(self):
        queryset_resource = AddressableUserQuerySetResource(mock_orm.QuerySet(
            User(pk=1, name='Alice', age=31),
            User(pk=2, name='Bob', age=20)
        ))

        model_resource = queryset_resource.get_child_resource(mock_context(), 999)
        self.assertIsNone(model_resource)


class ResourcePrepareTest(unittest.TestCase):
    class TestResource(resources.ModelResource):
        model_class = User
        fields = [
            fields.AttributeField(attribute='group.name', type=str),
            fields.AttributeField(attribute='domain.name', type=str)
        ]

    def test_prepare(self):
        related = resources.Related()

        queryset = self.TestResource.prepare(mock_context(), related)
        self.assertEqual(queryset._select, {
            'group',
            'domain'
        })

    def test_prepere_after_filter(self):
        """
        Django will reset related selects when a filter is added
        """
        queryset = MagicMock()
        queryset_resource = ComplexUserResourceQuerySetResource(queryset)

        queryset_resource.get(mock_context())
        calls = call.all().filter().select_related('manager').prefetch_related('reports').call_list()
        queryset.assert_has_calls(calls)


class DjangoUserResource(resources.ModelResource):
    '''
    Exists to test SchemaResource using Django's User model
    '''
    model_class = DjangoUser
    fields = [
        fields.AttributeField('date_joined', type=datetime),
        fields.AttributeField('email', type=str),
        fields.AttributeField('first_name', type=str),
        fields.RelatedManagerField('groups', None),
        fields.AttributeField('pk', type=int),
        fields.AttributeField('is_active', type=bool),
        fields.AttributeField('is_staff', type=bool),
        fields.AttributeField('is_superuser', type=bool),
        fields.AttributeField('last_login', type=datetime),
        fields.AttributeField('last_name', type=str),
        fields.AttributeField('password', type=str),
        fields.RelatedManagerField('user_permissions', None),
        fields.AttributeField('username', type=str)
    ]
    #TODO add filtering and sort order


class SchemaResourceTest(unittest.TestCase):
    def test_get(self):
        """
        Test GET request(s) for a model schema
        """
        self.maxDiff = None

        resource = resources.SchemaResource(DjangoUserResource)
        ctx = mock_context()
        ctx.build_resource_uri = lambda resource: 'uri://user/schema/'
        data = resource.get(ctx)

        #TODO add filtering and sort order
        expected = {
            'allowedDetailHttpMethods': ['get'],
            'allowedListHttpMethods': ['get'],
            'defaultFormat': 'application/json',
            'defaultLimit': 0,
            'filtering': {},
            'ordering': [],
            'resourceUri': 'uri://user/schema/',
            'fields': {
                'username': {
                    'nullable': False,
                    'default': u'',
                    'readonly': False,
                    'helpText': u'Required. 30 characters or fewer. Letters, numbers and @/./+/-/_ characters',
                    'blank': False,
                    'unique': True,
                    'type': 'str'
                },
                'lastLogin': {
                    'nullable': False,
                    'default': datetime.today().strftime("%Y-%m-%dT%H:%M:%S"),
                    'readonly': False,
                    'helpText': u'',
                    'blank': False,
                    'unique': False,
                    'type': 'datetime'
                },
                'firstName': {
                    'nullable': False,
                    'default': u'',
                    'readonly': False,
                    'helpText': u'',
                    'blank': True,
                    'unique': False,
                    'type': 'str'
                },
                'userPermissions': {
                    'nullable': False,
                    'default': u'',
                    'relatedType': 'to_many',
                    'readonly': False,
                    'helpText': u'Specific permissions for this user. Hold down "Control", or "Command" on a Mac, to select more than one.',
                    'blank': True,
                    'unique': False,
                    'type': 'related'
                },
                'lastName': {
                    'nullable': False,
                    'default': u'',
                    'readonly': False,
                    'helpText': u'',
                    'blank': True,
                    'unique': False,
                    'type': 'str'
                },
                'isSuperuser': {
                    'nullable': False,
                    'default': False,
                    'readonly': False,
                    'helpText': u'Designates that this user has all permissions without explicitly assigning them.',
                    'blank': True,
                    'unique': False,
                    'type': 'bool'
                },
                'dateJoined': {
                    'nullable': False,
                    'default': datetime.today().strftime("%Y-%m-%dT%H:%M:%S"),
                    'readonly': False,
                    'helpText': u'',
                    'blank': False,
                    'unique': False,
                    'type': 'datetime'
                },
                'isStaff': {
                    'nullable': False,
                    'default': False,
                    'readonly': False,
                    'helpText': u'Designates whether the user can log into this admin site.',
                    'blank': True,
                    'unique': False,
                    'type': 'bool'
                },
                'groups': {
                    'nullable': False,
                    'default': u'',
                    'relatedType': 'to_many',
                    'readonly': False,
                    'helpText': u'The groups this user belongs to. A user will get all permissions granted to each of his/her group. Hold down "Control", or "Command" on a Mac, to select more than one.',
                    'blank': True,
                    'unique': False,
                    'type': 'related'
                },
                'pk': {
                    'nullable': False,
                    'default': None,
                    'readonly': False,
                    'helpText': u'',
                    'blank': True,
                    'unique': True,
                    'type': 'int'
                },
                'password': {
                    'nullable': False,
                    'default': u'',
                    'readonly': False,
                    'helpText': u'',
                    'blank': False,
                    'unique': False,
                    'type': 'str'
                },
                'email': {
                    'nullable': False,
                    'default': u'',
                    'readonly': False,
                    'helpText': u'',
                    'blank': True,
                    'unique': False,
                    'type':
                    'str'
                },
                'isActive': {
                    'nullable': False,
                    'default': True,
                    'readonly': False,
                    'helpText': u'Designates whether this user should be treated as active. Unselect this instead of deleting accounts.',
                    'blank': True,
                    'unique': False,
                    'type': 'bool'
                }
            }
        }

        self.assertDictEqual(data, expected)
