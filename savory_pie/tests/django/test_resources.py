import json
import unittest
from mock import Mock, MagicMock, call, patch

from savory_pie.django import resources, fields, views
from savory_pie.tests.django import user_resource_schema, mock_orm, date_str
from savory_pie.tests.mock_context import mock_context
from savory_pie.resources import EmptyParams
from savory_pie import formatters

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
    name = Mock()
    age = Mock()


class UserOwner(mock_orm.Model):
    user = Mock(django.db.models.fields.related.ReverseSingleRelatedObjectDescriptor(Mock()))
    name = Mock()


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


class SemiUnaddressableUserResource(UnaddressableUserResource):
    parent_resource_path = 'users'


class ComplexUserResource(resources.ModelResource):
    model_class = User

    fields = [
        fields.SubModelResourceField(attribute='manager', resource_class=UnaddressableUserResource),
        fields.RelatedManagerField(attribute='reports', resource_class=UnaddressableUserResource)
    ]


class UserOwnerResource(resources.ModelResource):
    model_class = UserOwner

    fields = [
        fields.AttributeField(attribute='name', type=str),
    ]


class ComplexUserRelationResource(resources.ModelResource):
    model_class = User

    owner_field = fields.SubModelResourceField(attribute='owner', resource_class=UserOwnerResource)

    fields = [
        fields.AttributeField(attribute='name', type=str),
        fields.AttributeField(attribute='age', type=int),
        owner_field,
    ]


class ModelResourceTest(unittest.TestCase):
    def make_request(self, _json, sha=None):
        request = Mock()
        request.META = Mock()
        request.META.get.return_value = sha
        request.read.return_value = _json
        return request

    def test_resource_path(self):
        user = User(pk=1, name='Bob', age=20)
        resource = AddressableUserResource(user)

        self.assertEqual(resource.resource_path, 'users/1')

    @patch('savory_pie.django.resources.dirty_bits')
    def test_dirty_signal_register(self, dirty_bits):
        class NewClazz(mock_orm.Model):
            pass

        class NewClazzResource(resources.ModelResource):
            model_class = NewClazz

        NewClazzResource(NewClazz())
        dirty_bits.register.assert_called_with(NewClazz)

    def test_get(self):
        user = User(pk=1, name='Bob', age=20)

        resource = AddressableUserResource(user)
        dct = resource.get(mock_context(), EmptyParams())

        self.assertEqual(dct, {
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

    def test_complex_put(self):
        user = User()
        user._meta.get_field().related.field.name = 'name'
        user.owner = UserOwner()

        resource = ComplexUserRelationResource(user)
        resource.put(mock_context(), {
            'name': 'Bob',
            'age': 20,
            'owner': {'name': 'bob owner'},
        })

        self.assertTrue(user.save.called)
        self.assertTrue(user.owner.save.called)
        self.assertEqual(user.name, 'Bob')
        self.assertEqual(user.age, 20)
        self.assertEqual(user.owner.name, 'bob owner')

    def test_clean_save(self):

        class DirtyUser(mock_orm.Model):
            age = 30
            name = 'Bob'
            _fields = ['age', 'name']
            pk = 3

        class DirtyUserResource(resources.ModelResource):
            parent_resource_path = 'users'
            model_class = DirtyUser

            fields = [
                fields.AttributeField(attribute='name', type=str),
                fields.AttributeField(attribute='age', type=int)
            ]

        dirty_user = DirtyUser()
        dirty_user.save = Mock()
        resource = DirtyUserResource(dirty_user)

        resource.put(mock_context(), {
            'name': 'Bob',
            'age': 30,
            'resourceUri': 'uri://users/1'
        })
        self.assertFalse(dirty_user.save.called)

    def test_dirty_save(self):
        class DirtyUser(mock_orm.Model):
            age = 30
            name = 'Bob'
            _fields = ['age', 'name']
            pk = 3

        class DirtyUserResource(resources.ModelResource):
            parent_resource_path = 'users'
            model_class = DirtyUser

            fields = [
                fields.AttributeField(attribute='name', type=str),
                fields.AttributeField(attribute='age', type=int)
            ]

        dirty_user = DirtyUser()
        dirty_user.save = Mock()
        resource = DirtyUserResource(dirty_user)

        resource.put(mock_context(), {
            'name': 'Bob',
            'age': 33,
            'resourceUri': 'uri://users/1'
        })
        self.assertTrue(dirty_user.save.called)

    def test_qsr_returns_hashes(self):
        resource = AddressableUserQuerySetResource(mock_orm.QuerySet(
            User(pk=1, name='Alice', age=31),
            User(pk=2, name='Bob', age=20)
        ))
        data = resource.get(mock_context(), EmptyParams())

        self.assertEqual(data['meta'], {
            'resourceUri': 'uri://users',
            'count': 2
        })

        self.assertEqual(data['objects'][0]['$hash'], 'aa29a35c3d5f0a3de7fae2f1f2b30c0e1b35084f')
        self.assertEqual(data['objects'][1]['$hash'], 'bbb39a0ea490e5afe9cd547dc7b96572f5ab7fd7')

    def test_put_with_good_sha(self):
        user = User()
        resource = AddressableUserResource(user)
        resource.get = lambda *args: {"age": 20, "name": "Bob"}
        request = self.make_request('{"age": 20, "name": "Bob"}', 'fd92376f24d6a75974c8da6edf84a834b92ee13c')
        response = views._process_put(mock_context(), resource, request)
        self.assertEqual(response.status_code, 204)

    def test_put_with_bad_sha(self):
        user = User()
        resource = AddressableUserResource(user)
        resource.get = lambda *args: {"age": 20, "name": "Bob"}
        request = self.make_request('{"age": 20, "name": "Bob"}', 'OmManePadmeHumOmManePadmeHumOmManePadmeHum')
        response = views._process_put(mock_context(), resource, request)
        self.assertEqual(response.status_code, 412)

    def test_put_with_missing_required_field(self):
        user = User()
        request = self.make_request('{"name": "Bob"}')   # no age
        response = views._process_put(mock_context(),
                                      AddressableUserResource(user),
                                      request)
        errors = json.loads(response.content)
        self.assertTrue('validation_errors' in errors)
        self.assertEqual(errors['validation_errors'], {'missingField': 'age', 'target': 'User'})

    def test_put_with_foreign_key_none_resource(self):
        user = User()

        resource = ComplexUserRelationResource(user)
        resource.put(mock_context(), {
            'name': 'Bob',
            'age': 20,
            'owner': {'name': 'bob owner'},
        })

        self.assertTrue(user.save.called)
        self.assertTrue(user.owner.save.called)
        self.assertEqual(user.name, 'Bob')
        self.assertEqual(user.age, 20)
        self.assertEqual(user.owner.name, 'bob owner')

    def test_put_with_save_false(self):
        user = User()

        resource = AddressableUserResource(user)
        resource.put(mock_context(), {
            'name': 'Bob',
            'age': 20
        }, save=False)

        self.assertEqual(user.name, 'Bob')
        self.assertEqual(user.age, 20)
        self.assertFalse(user.save.called)

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

    def test_pre_save_optional(self):
        user = Mock(name='user')
        field = Mock(['handle_incoming'])

        class Resource(resources.ModelResource):
            model_class = User
            fields = [field]
        resource = Resource(user)

        resource.put(mock_context(), {'foo': 'bar'})

        user.save.assert_called_with()

    def test_save_fields(self):
        user = Mock(name='user')
        field = Mock(['handle_incoming', 'save'])

        class Resource(resources.ModelResource):
            model_class = User
            fields = [field]
        resource = Resource(user)

        resource.put(mock_context(), {'foo': 'bar'})

        self.assertTrue(field.save.called)

    def test_save_fields_optional(self):
        user = Mock(name='user')
        field = Mock(['handle_incoming'])

        class Resource(resources.ModelResource):
            model_class = User
            fields = [field]
        resource = Resource(user)

        # Tests that an attribute error is not raised
        resource.put(mock_context(), {'foo': 'bar'})


class AddressableUserQuerySetResource(resources.QuerySetResource):
    resource_class = AddressableUserResource


class SemiUnaddressableUserQuerySetResource(resources.QuerySetResource):
    resource_class = SemiUnaddressableUserResource


class FullyUnaddressableUserQuerySetResource(resources.QuerySetResource):
    resource_class = UnaddressableUserResource


class ComplexUserResourceQuerySetResource(resources.QuerySetResource):
    resource_class = ComplexUserResource


class QuerySetResourceTest(unittest.TestCase):
    def remove_hash(self, dct):
        return dict((k, v) for k, v in dct.items() if k[:1] != '$')

    def test_get(self):
        resource = AddressableUserQuerySetResource(mock_orm.QuerySet(
            User(pk=1, name='Alice', age=31),
            User(pk=2, name='Bob', age=20)
        ))
        data = resource.get(mock_context(), EmptyParams())

        self.assertEqual(data['meta'], {
            'resourceUri': 'uri://users',
            'count': 2
        })

        self.assertEqual(map(self.remove_hash, data['objects']), [
            {'resourceUri': 'uri://users/2', 'name': 'Bob', 'age': 20},
            {'resourceUri': 'uri://users/1', 'name': 'Alice', 'age': 31}
        ])

    def test_get_distinct(self):
        resource = AddressableUserQuerySetResource(mock_orm.QuerySet(
            User(pk=1, name='Alice', age=31),
            User(pk=1, name='Alice', age=31)
        ))
        data = resource.get(mock_context(), EmptyParams())
        self.assertEqual(data['meta'], {
            'resourceUri': 'uri://users',
            'count': 1
        })

        self.assertEqual(map(self.remove_hash, data['objects']), [
            {'resourceUri': 'uri://users/1', 'name': 'Alice', 'age': 31},
        ])

    def test_empty_queryset(self):
        mock_query_set = MagicMock()
        mock_query_set.__bool__ = False
        mock_query_set.return_value = None
        resource = AddressableUserQuerySetResource(mock_query_set)
        data = resource.get(mock_context(), EmptyParams())

        self.assertEqual(data['meta'], {
            'resourceUri': 'uri://users',
            'count': 0
        })

        self.assertEqual(data['objects'], [])

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

    def test_prepare_optional(self):
        class NoopField(object):
            def handle_incoming(self, ctx, source_dict, target_obj):
                pass

            def handle_outgoing(self, ctx, source_obj, target_dict):
                pass

        class TestResource(resources.ModelResource):
            model_class = User
            fields = [
                NoopField(),
            ]

        related = resources.Related()
        # Will not raise an error
        TestResource.prepare(mock_context(), related)

    def test_prepere_after_filter(self):
        """
        Django will reset related selects when a filter is added
        """
        queryset = MagicMock()
        queryset_resource = ComplexUserResourceQuerySetResource(queryset)

        queryset_resource.get(mock_context(), EmptyParams())
        calls = call.all().distinct().filter().select_related('manager').prefetch_related('reports').call_list()
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

    def setUp(self):
        self.json_formatter = formatters.JSONFormatter()

    def do_assert_date_equal(self, key):
        field = self.do_get()['fields'][key]
        field['default'] = date_str

        self.assertDictEqual(field, user_resource_schema['fields'][key])

    def do_assert_equal(self, key, assert_type=''):
        getattr(self, 'assert{}Equal'.format(assert_type))(self.do_get()[key], user_resource_schema[key])

    def do_assert_field_equal(self, key):
        self.assertDictEqual(self.do_get()['fields'][key], user_resource_schema['fields'][key])

    def do_get(self):
        """
        Make GET request, return response
        """
        resource = resources.SchemaResource(DjangoUserResource)
        ctx = mock_context()
        ctx.build_resource_uri = lambda resource: 'uri://user/schema/'
        return resource.get(ctx)

    def test_get(self):
        """
        Test basic GET request for a SchemaResource
        """
        self.assertIsInstance(self.do_get(), dict)

    def test_allowed_detail_http_methods(self):
        self.do_assert_equal('allowedDetailHttpMethods', assert_type='List')

    def test_allowed_list_http_methods(self):
        self.do_assert_equal('allowedListHttpMethods', assert_type='List')

    def test_default_format(self):
        self.do_assert_equal('defaultFormat')

    def test_default_limit(self):
        self.do_assert_equal('defaultLimit')

    def test_filtering(self):
        self.do_assert_equal('filtering', assert_type='Dict')

    def test_ordering(self):
        self.do_assert_equal('ordering', assert_type='List')

    def test_resource_uri(self):
        self.do_assert_equal('resourceUri')

    def test_fields_length(self):
        self.assertEqual(len(self.do_get()['fields']), len(user_resource_schema['fields']))

    def test_field_date_joined(self):
        self.do_assert_date_equal('dateJoined')

    def test_field_email(self):
        self.do_assert_field_equal('email')

    def test_field_first_name(self):
        self.do_assert_field_equal('firstName')

    def test_field_groups(self):
        self.do_assert_field_equal('groups')

    def test_field_is_active(self):
        self.do_assert_field_equal('isActive')

    def test_field_is_staff(self):
        self.do_assert_field_equal('isStaff')

    def test_field_is_superuser(self):
        self.do_assert_field_equal('isSuperuser')

    def test_field_last_login(self):
        self.do_assert_date_equal('lastLogin')

    def test_field_last_name(self):
        self.do_assert_field_equal('lastName')

    def test_field_password(self):
        self.do_assert_field_equal('password')

    def test_field_pk(self):
        self.do_assert_field_equal('pk')

    def test_field_username(self):
        self.do_assert_field_equal('username')

    def test_field_user_permissions(self):
        self.do_assert_field_equal('userPermissions')
