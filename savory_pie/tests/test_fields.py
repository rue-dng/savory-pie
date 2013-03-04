import unittest
from mock import Mock, MagicMock

from django.core.exceptions import ObjectDoesNotExist

from savory_pie.django_utils import Related
from savory_pie.resources import ModelResource, QuerySetResource
from savory_pie.fields import (
    AttributeField,
    SubModelResourceField,
    RelatedManagerField,
    URIResourceField
)
from savory_pie.tests import mock_orm

from savory_pie.tests.mock_context import mock_context


class AttributeFieldTest(unittest.TestCase):
    def test_simple_outgoing(self):
        source_object = Mock()
        source_object.foo = 20

        target_dict = dict()

        field = AttributeField(attribute='foo', type=int)
        field.handle_outgoing(mock_context(), source_object, target_dict)

        self.assertEqual(target_dict['foo'], 20)

    def test_simple_none_outgoing(self):
        source_object = Mock()
        source_object.foo = None

        target_dict = dict()

        field = AttributeField(attribute='foo', type=int)
        field.handle_outgoing(mock_context(), source_object, target_dict)

        self.assertEqual(target_dict['foo'], None)

    def test_multilevel_outgoing(self):
        source_object = Mock()
        source_object.foo.bar = 20

        field = AttributeField(attribute='foo.bar', type=int)

        target_dict = dict()

        field.handle_outgoing(mock_context(), source_object, target_dict)

        self.assertEqual(target_dict['bar'], 20)

    def test_multilevel_incoming(self):
        source_dict = {
            'bar': 20
        }

        field = AttributeField(attribute='foo.bar', type=int)

        target_object = Mock(name='target')

        field.handle_incoming(mock_context(), source_dict, target_object)

        self.assertEqual(target_object.foo.bar, 20)

    def test_simple_incoming(self):
        source_dict = {
            'foo': 20
        }

        target_object = Mock(name='target')

        field = AttributeField(attribute='foo', type=int)
        field.handle_incoming(mock_context(), source_dict, target_object)

        self.assertEqual(target_object.foo, 20)

    def test_incoming_read_only(self):
        source_dict = {
            'foo': 20
        }

        target_object = Mock(name='target', spec=[])

        field = AttributeField(attribute='foo', type=int, read_only=True)
        field.handle_incoming(mock_context(), source_dict, target_object)

        self.assertFalse(hasattr(target_object, 'foo'))

    def test_simple_none_incoming(self):
        source_dict = {
            'foo': None
        }

        target_object = Mock(name='target')

        field = AttributeField(attribute='foo', type=int)
        field.handle_incoming(mock_context(), source_dict, target_object)

        self.assertEqual(target_object.foo, None)

    def test_simple_missing_incoming(self):
        source_dict = {}

        target_object = Mock(name='target')

        field = AttributeField(attribute='foo', type=int)
        with self.assertRaises(KeyError):
            field.handle_incoming(mock_context(), source_dict, target_object)

    def test_alternate_name_outgoing(self):
        source_object = Mock()
        source_object.foo.bar = 20

        field = AttributeField(attribute='foo.bar', type=int, published_property='foo')

        target_dict = dict()

        field.handle_outgoing(mock_context(), source_object, target_dict)

        self.assertEqual(target_dict['foo'], 20)

    def test_alternate_name_incoming(self):
        source_dict = {
            'foo': 20
        }

        field = AttributeField(attribute='foo.bar', type=int, published_property='foo')

        target_object = Mock(name='target')

        field.handle_incoming(mock_context(), source_dict, target_object)

        self.assertEqual(target_object.foo.bar, 20)

    def test_prepare(self):
        field = AttributeField(attribute='foo.bar.baz', type=int)

        related = Related()
        field.prepare(mock_context(), related)

        self.assertEqual(related._select, {
            'foo__bar'
        })

    def test_prepare_with_use_prefetch(self):
        field = AttributeField(attribute='foo.bar.baz', type=int, use_prefetch=True)

        related = Related()
        field.prepare(mock_context(), related)

        self.assertEqual(related._prefetch, {
            'foo__bar'
        })

    def test_add_field(self):
        field = AttributeField(attribute='foo', type=int)
        source_dict = {'foo': 3}
        filter_args = {}

        field.add_filter(mock_context(), filter_args, source_dict)

        self.assertEqual({'foo': 3}, filter_args)



class URIResourceFieldTest(unittest.TestCase):
    def test_outgoing(self):

        class Resource(ModelResource):
            parent_resource_path = 'resources'

        field = URIResourceField(attribute='foo', resource_class=Resource)

        source_object = Mock()
        source_object.foo = mock_orm.Model(pk=2)

        target_dict = dict()
        field.handle_outgoing(mock_context(), source_object, target_dict)

        self.assertEqual(target_dict['foo'], 'uri://resources/2')

    def test_incoming(self):

        class Resource(ModelResource):
            pass

        field = URIResourceField(attribute='foo', resource_class=Resource)

        source_dict = {
            'foo': 'uri://resources/2'
        }
        target_object = Mock()

        related_model = mock_orm.Model(pk=2)

        ctx = mock_context()
        ctx.resolve_resource_uri = Mock(return_value=Resource(related_model))

        field.handle_incoming(ctx, source_dict, target_object)

        ctx.resolve_resource_uri.assert_called_with('uri://resources/2')
        self.assertEqual(target_object.foo, related_model)

    def test_incoming_read_only(self):

        class Resource(ModelResource):
            pass

        field = URIResourceField(
            attribute='foo',
             resource_class=Resource,
             read_only=True,
        )

        source_dict = {
            'foo': 'uri://resources/2'
        }
        target_object = Mock([])

        related_model = mock_orm.Model(pk=2)

        ctx = mock_context()
        ctx.resolve_resource_uri = Mock(return_value=Resource(related_model))

        field.handle_incoming(ctx, source_dict, target_object)

        self.assertFalse(ctx.resolve_resource_uri.called)
        self.assertFalse(hasattr(target_object, 'foo'))


class SubModelResourceFieldTest(unittest.TestCase):
    def test_outgoing(self):

        class Resource(ModelResource):
            fields = [
                AttributeField(attribute='bar', type=int),
            ]

        field = SubModelResourceField(attribute='foo', resource_class=Resource)

        source_object = Mock()
        source_object.foo.bar = 20

        target_dict = dict()

        field.handle_outgoing(mock_context(), source_object, target_dict)

        self.assertEqual(target_dict['foo'], {'bar': 20})

    def test_incoming_update_existing(self):

        class Resource(ModelResource):
            model_class = Mock()
            fields = [
                AttributeField(attribute='bar', type=int),
            ]

        field = SubModelResourceField(attribute='foo', resource_class=Resource)

        source_dict = {
            'foo': {'bar': 20},
        }

        target_object = Mock()

        field.handle_incoming(mock_context(), source_dict, target_object)

        self.assertEqual(20, target_object.foo.bar)
        target_object.foo.save.assert_called_with()

    def test_incoming_read_only(self):

        class Resource(ModelResource):
            model_class = Mock(spec=[])
            fields = [
                AttributeField(attribute='bar', type=int),
            ]

        field = SubModelResourceField(
            attribute='foo',
            resource_class=Resource,
            read_only=True,
        )

        source_dict = {
            'foo': {'bar': 20},
        }

        target_object = Mock()
        target_object.foo = Mock(['save'])

        field.handle_incoming(mock_context(), source_dict, target_object)

        self.assertFalse(hasattr(target_object.foo, 'bar'))
        self.assertFalse(target_object.foo.save.called)

    def test_new_object_incoming(self):

        class MockResource(ModelResource):
            model_class = Mock()
            fields = [
                AttributeField(attribute='bar', type=int),
            ]

            @classmethod
            def get_by_source_dict(cls, ctx, sub_source_dict):
                return None

        field = SubModelResourceField(attribute='foo', resource_class=MockResource)

        source_dict = {
            'foo': {'bar': 20},
        }

        # The django ORM makes me sad that this is not a None or AttributeError
        class MockFailsOnFooAccess(Mock):
            def __getattr__(self, name):
                if name == 'foo':
                    raise ObjectDoesNotExist
                else:
                    return super(Mock, self).__getattr__(name)

        target_object = MockFailsOnFooAccess()
        field.handle_incoming(mock_context(), source_dict, target_object)

        self.assertEqual(20, target_object.foo.bar)
        self.assertEqual(MockResource.model_class.return_value, target_object.foo)
        target_object.foo.save.assert_called()

    def test_find_existing_incoming(self):

        mock_model = Mock()

        class MockResource(ModelResource):
            model_class = Mock()
            fields = [
                AttributeField(attribute='bar', type=int),
            ]

            @classmethod
            def get_by_source_dict(cls, ctx, sub_source_dict):
                return cls(mock_model)

        field = SubModelResourceField(attribute='foo', resource_class=MockResource)

        source_dict = {
            'foo': {'bar': 20},
        }

        # The django ORM makes me sad that this is not a None or AttributeError
        class MockFailsOnFooAccess(Mock):
            def __getattr__(self, name):
                if name == 'foo':
                    raise ObjectDoesNotExist
                else:
                    return super(Mock, self).__getattr__(name)

        target_object = MockFailsOnFooAccess()
        field.handle_incoming(mock_context(), source_dict, target_object)

        self.assertEqual(20, target_object.foo.bar)
        self.assertEqual(mock_model, target_object.foo)
        target_object.foo.save.assert_called()

    def test_prepare(self):
        class MockResource(ModelResource):
            model_class = Mock()
            fields = [
                AttributeField(attribute='bar.baz', type=int),
            ]

        field = SubModelResourceField(attribute='foo', resource_class=MockResource)

        related = Related()
        field.prepare(mock_context(), related)

        self.assertEqual(related._select, {
            'foo',
            'foo__bar'
        })

    def test_prepare_with_use_prefetch(self):
        class MockResource(ModelResource):
            model_class = Mock()
            fields = [
                AttributeField(attribute='bar.baz', type=int),
            ]

        field = SubModelResourceField(
            attribute='foo',
            resource_class=MockResource,
            use_prefetch=True
        )

        related = Related()
        field.prepare(mock_context(), related)

        self.assertEqual(related._prefetch, {
            'foo',
            'foo__bar'
        })

class RelatedManagerFieldTest(unittest.TestCase):
    def test_outgoing(self):

        class MockResource(ModelResource):
            model_class = mock_orm.Model
            fields = [
                AttributeField(attribute='bar', type=int),
            ]

        field = RelatedManagerField(attribute='foo', resource_class=MockResource)

        source_object = mock_orm.Model()
        related_manager = mock_orm.Manager()
        related_manager.all = Mock(return_value=mock_orm.QuerySet(
            mock_orm.Model(pk=4, bar=14)
        ))
        source_object.foo = related_manager

        target_dict = {}
        field.handle_outgoing(mock_context(), source_object, target_dict)
        self.assertEqual([{'_id': '4', 'bar': 14}], target_dict['foo'])

    def test_prepare(self):

        class MockResource(ModelResource):
            model_class = mock_orm.Model
            fields = [
                AttributeField('bar.baz', type=int)
            ]

        class MockQuerySetResource(QuerySetResource):
            resource_class = MockResource

        field = RelatedManagerField(attribute='foo', resource_class=MockQuerySetResource)

        related = Related()
        field.prepare(mock_context(), related)

        self.assertEqual(related._prefetch, {
            'foo',
            'foo__bar'
        })

    def test_incoming_no_id(self):
        del mock_orm.Model._models[:]

        class MockResource(ModelResource):
            model_class = mock_orm.Model
            fields = [
                AttributeField(attribute='bar', type=int),
            ]

        field = RelatedManagerField(attribute='foo', resource_class=MockResource)

        target_obj = mock_orm.Mock()
        related_manager = mock_orm.Manager()
        related_manager.all = Mock(return_value=mock_orm.QuerySet())
        target_obj.foo = related_manager
        source_dict = {
            'foo': [{'bar': 4}],
        }

        model_index = len(mock_orm.Model._models)
        field.handle_incoming(mock_context(), source_dict, target_obj)

        model = mock_orm.Model._models[model_index]
        self.assertEqual(4, model.bar)
        related_manager.add.assert_called_with(model)

    def test_incoming_delete(self):
        del mock_orm.Model._models[:]

        class MockResource(ModelResource):
            model_class = mock_orm.Model
            fields = [
                AttributeField(attribute='bar', type=int),
            ]

        field = RelatedManagerField(attribute='foo', resource_class=MockResource)

        target_obj = mock_orm.Mock()
        related_manager = mock_orm.Manager()
        related_model = mock_orm.Model(pk=4, bar=14)
        related_manager.all = Mock(return_value=mock_orm.QuerySet(
            related_model
        ))
        target_obj.foo = related_manager
        source_dict = {
            'foo': [],
        }

        field.handle_incoming(mock_context(), source_dict, target_obj)

        related_manager.remove.assert_called_with(related_model)

    def test_incoming_delete_non_null(self):
        del mock_orm.Model._models[:]

        class MockResource(ModelResource):
            model_class = mock_orm.Model
            fields = [
                AttributeField(attribute='bar', type=int),
            ]

        field = RelatedManagerField(attribute='foo', resource_class=MockResource)

        target_obj = mock_orm.Mock()
        related_manager = mock_orm.Manager()
        related_manager.mock_add_spec(['add'])
        related_manager.all = Mock(return_value=mock_orm.QuerySet(
            mock_orm.Model(pk=4, bar=14)
        ))
        target_obj.foo = related_manager
        source_dict = {
            'foo': [],
        }

        field.handle_incoming(mock_context(), source_dict, target_obj)

        model = mock_orm.Model._models[0]
        model.delete.assert_called_with()

    def test_incoming_edit(self):
        del mock_orm.Model._models[:]

        class MockResource(ModelResource):
            model_class = mock_orm.Model
            fields = [
                AttributeField(attribute='bar', type=int),
            ]

        field = RelatedManagerField(attribute='foo', resource_class=MockResource)

        target_obj = mock_orm.Mock()
        related_manager = mock_orm.Manager()
        related_model = mock_orm.Model(pk=4, bar=14)
        related_manager.all = Mock(return_value=mock_orm.QuerySet(
            related_model
        ))
        target_obj.foo = related_manager
        source_dict = {
            'foo': [{'_id': '4', 'bar': 15}],
        }

        model_index = len(mock_orm.Model._models) + 1
        field.handle_incoming(mock_context(), source_dict, target_obj)

        self.assertEqual(15, related_model.bar)
        related_model.save.assert_called()

    def test_incoming_read_only(self):
        del mock_orm.Model._models[:]

        class MockResource(ModelResource):
            model_class = mock_orm.Model
            fields = [
                AttributeField(attribute='bar', type=int),
            ]

        field = RelatedManagerField(
            attribute='foo',
            resource_class=MockResource,
            read_only=True,
        )

        target_obj = mock_orm.Mock()
        related_manager = mock_orm.Manager()
        related_model = mock_orm.Model(pk=4, bar=14)
        related_manager.all = Mock(return_value=mock_orm.QuerySet(
            related_model
        ))
        target_obj.foo = related_manager
        source_dict = {
            'foo': [{'_id': '4', 'bar': 15}],
        }

        field.handle_incoming(mock_context(), source_dict, target_obj)

        self.assertEqual(14, related_model.bar)
        self.assertFalse(related_model.save.called)

