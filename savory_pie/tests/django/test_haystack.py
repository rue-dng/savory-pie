import unittest

import mock

from django.db import models

from savory_pie.formatters import JSONFormatter
from savory_pie.django.haystack_filter import HaystackFilter
from savory_pie.django.resources import HaystackSearchResource
from savory_pie.django.haystack_field import HaystackField
from savory_pie.tests.mock_context import mock_context
from test_filters import Params


class TestModel(models.Model):
    pass


class HaystackFilterTest(unittest.TestCase):

    @mock.patch('savory_pie.django.haystack_filter.SearchQuerySet')
    def test_simple_filter(self, haystack_qs_cls):
        result1 = mock.Mock(name='result1', pk=1)
        result2 = mock.Mock(name='result2', pk=2)

        haystack_qs = haystack_qs_cls.return_value
        haystack_qs.filter.return_value = haystack_qs
        haystack_qs.models.return_value = haystack_qs
        haystack_qs.__iter__ = lambda x: iter([result1, result2])

        queryset = mock.Mock(name='queryset')
        queryset.model = TestModel

        haystack_filter = HaystackFilter()
        haystack_filter.filter(
            mock_context(),
            Params({'q': 'foo'}),
            queryset,
        )

        queryset.assert_has_calls(
            [
                mock.call.filter(pk__in=[1, 2]),
            ],
            any_order=True,
        )

        haystack_qs.assert_has_calls(
            [
                mock.call.models(TestModel),
                mock.call.filter(content=u'foo'),
            ],
            any_order=True
        )

    @mock.patch('savory_pie.django.haystack_filter.SearchQuerySet')
    def test_multi_word_filter(self, haystack_qs_cls):
        haystack_qs = haystack_qs_cls.return_value
        haystack_qs.filter.return_value = haystack_qs
        haystack_qs.models.return_value = haystack_qs

        queryset = mock.Mock(name='queryset')
        queryset.model = TestModel

        haystack_filter = HaystackFilter()
        haystack_filter.filter(
            mock_context(),
            Params({'q': 'foo bar baz'}),
            queryset,
        )

        haystack_qs.assert_has_calls(
            [
                mock.call.filter(content=u'foo'),
                mock.call.filter(content=u'bar'),
                mock.call.filter(content=u'baz'),
                mock.call.models(TestModel),
            ],
            any_order=True
        )


class HaystackSearchResourceTest(unittest.TestCase):

    @mock.patch('__builtin__.enumerate')
    @mock.patch('savory_pie.django.resources.SearchQuerySet')
    def test_haystack_search_resource(self, haystack_qs_cls, enum_mock):
        n = 3
        haystack_qs_cls.return_value = haystack_qs = mock.Mock()
        haystack_qs.filter.return_value = haystack_qs
        haystack_qs.models.return_value = haystack_qs
        haystack_qs.count.return_value = n

        enum_mock.get_stored_fields.return_value = enum_mock
        enum_mock.__getitem__.return_value = '"api-as-string"'
        enum_mock.return_value = [(i, enum_mock) for i in range(n)]

        sr = HaystackSearchResource()
        sr.model_class = TestModel
        ctx = mock.Mock()
        self.assertEqual(
            ''.join([x for x in sr.get(ctx, {'q': 'foo'})]),
            '{"meta":{"count":3},"objects":["api-as-string","api-as-string","api-as-string"]}')
        haystack_qs.models.assert_called_with(TestModel)
        haystack_qs.count.assert_called_with()


class HaystackFieldTest(unittest.TestCase):

    def test_haystack_field(self):
        FooResource = mock.Mock()
        FooResource.return_value = frv = mock.Mock()
        frv.get.return_value = {'a': 'b'}
        api = HaystackField(
            base_uri='/my/api/path/',
            formatter=JSONFormatter(),
            resource=FooResource)
        self.assertEqual(api.prepare(None), '{"a": "b", "$stale": true}')
