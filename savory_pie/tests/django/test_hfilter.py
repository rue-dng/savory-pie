import unittest

import mock
from django.db import models

from savory_pie.tests.mock_context import mock_context
from savory_pie.django.haystack_filter import HaystackFilter
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
