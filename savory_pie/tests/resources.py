import unittest
import mock_orm
import django.db.models.query
from savory_pie import resources, fields
from savory_pie.formatters import JSONFormatter

from mock import Mock

def mock_context():
    ctx = Mock(name='context', spec=[])
    ctx.formatter = JSONFormatter()
    ctx.build_resource_uri = lambda resource: 'uri://' + resource.resource_path
    return ctx


class ResourceTest(unittest.TestCase):
    def no_allowed_methods(self):
        resource = resources.Resource()
        self.assertEqual(resource.allowed_methods, set())

    def allows_get(self):
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


class AddressableUserQuerySetResource(resources.QuerySetResource):
    resource_path = 'users'
    resource_class = AddressableUserResource


class SemiUnaddressableUserQuerySetResource(resources.QuerySetResource):
    resource_path = 'users'
    resource_class = UnaddressableUserResource


class FullyUnaddressableUserQuerySetResource(resources.QuerySetResource):
    resource_class = UnaddressableUserResource


class RelatedTest(unittest.TestCase):
    def test_select(self):
        related = resources.Related()

        related.select('foo')
        self.assertEqual(related._select, {
            'foo'
        })

        related.select('bar')
        self.assertEqual(related._select, {
            'foo',
            'bar'
        })

    def test_prefetch(self):
        related = resources.Related()

        related.prefetch('foo')
        self.assertEqual(related._prefetch, {
            'foo'
        })

        related.prefetch('bar')
        self.assertEqual(related._prefetch, {
            'foo',
            'bar'
        })

    def test_sub_select(self):
        related = resources.Related()
        sub_related = related.sub_select('foo')

        sub_related.select('bar')
        sub_related.prefetch('baz')

        self.assertEqual(related._select, {
            'foo__bar'
        })
        self.assertEqual(related._prefetch, {
            'foo__baz'
        })

    def test_sub_prefetch(self):
        related = resources.Related()
        sub_related = related.sub_prefetch('foo')

        sub_related.select('bar')
        sub_related.prefetch('baz')

        self.assertEqual(related._select, set())
        # Because foo is assumed to have a non-one cardinality, sub-selects
        # through foo are also converted into prefetch-es.  In this case, bar.
        self.assertEqual(related._prefetch, {
            'foo__bar',
            'foo__baz'
        })

    def test_sub_prefetch_continuation(self):
        related = resources.Related()
        sub_related = related.sub_prefetch('foo')
        sub_sub_related = sub_related.sub_select('bar')

        sub_sub_related.select('baz')

        # Because foo was prefetch, the sub-select of bar is also forced into
        # prefetch mode, so foo__bar__baz ends up being prefetched.
        self.assertEqual(related._prefetch, {
            'foo__bar__baz'
        })

    def test_empty_prepare(self):
        related = resources.Related()

        queryset = related.prepare(mock_orm.QuerySet())

        self.assertEqual(queryset._selected, set())
        self.assertEqual(queryset._prefetched, set())

    def test_prepare(self):
        related = resources.Related()

        related.select('foo')
        related.prefetch('bar')

        queryset = related.prepare(mock_orm.QuerySet())

        self.assertEqual(queryset._selected, {
            'foo'
        })
        self.assertEqual(queryset._prefetched, {
            'bar'
        })


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
