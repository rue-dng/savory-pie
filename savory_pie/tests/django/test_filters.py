import unittest
from mock import Mock
from django.http import QueryDict

from savory_pie.django import  filters
from savory_pie.tests.django import mock_orm
from savory_pie.tests.mock_context import mock_context

import savory_pie.formatters


class MockUser(mock_orm.Model):
    pass


class TestParams(object):

    def __init__(self, *args):
        # we need our query string to be camel cased, since in StandardFilter, we convert these strings
        # Note, since we are calling default_publish_property on the filter names,
        # it turns name_exact=Alice to nameExact=alice, so I made all the query strings like 'Alice' to be lower cased 'alice'
        formatted_names = []
        for name in args:
            formatted_names.append(savory_pie.formatters.JSONFormatter().default_published_property(name))

        self.querystring = "&".join(formatted_names)
        self._GET = QueryDict(self.querystring)


_users = mock_orm.QuerySet(
    MockUser(pk=1, name='alice', age=31),
    MockUser(pk=2, name='charlie', age=26),
    MockUser(pk=3, name='bob', age=20)
)

MockUser.objects.all = Mock(return_value=_users)

_filters = [
	filters.StandardFilter('official_test_user', {'name': 'alice'}),
	filters.StandardFilter('bogus_test_user', {'name': 'Nobody'}),
	filters.StandardFilter('early_name', {'name__lt': 'c00000'}),
	filters.StandardFilter('younger_only', {'age__lt': 25}),
	filters.StandardFilter('older_only', {'age__gt': 25}),
	filters.StandardFilter('alphabetical', {}, order_by=['name']),
	filters.StandardFilter('reverse_alphabetical', {}, order_by=['-name']),
	filters.ParameterizedFilter('name_exact', 'name'),
]


class FilterTest(unittest.TestCase):

    def apply_filters(self, *filternames):
        ctx = mock_context()
        queryset = _users

        params = TestParams(*filternames)

        for filter in _filters:
            queryset = filter.filter(ctx, params, queryset)
        return queryset


class StandardFilterTest(FilterTest):

    def test_without_filtering(self):
        results = self.apply_filters()
        self.assertEqual(3, results.count())
        self.assertEqual(['alice', 'charlie', 'bob'], [x.name for x in results])

    def test_good_filter(self):
        results = self.apply_filters('official_test_user=')
        self.assertEqual(1, results.count())
        self.assertEqual(['alice'], [x.name for x in results])

    def test_bad_filter(self):
        results = self.apply_filters('bogus_test_user=')
        self.assertEqual(0, results.count())
        self.assertEqual([], [x.name for x in results])

    def test_multiple_filters(self):
        results = self.apply_filters('official_test_user=', 'early_name=')
        # older_only: alice,charlie,bob -> alice,charlie
        # early_name: alice,charlie -> alice
        self.assertEqual(1, results.count())
        self.assertEqual(['alice'], [x.name for x in results])

    def test_gt_filter(self):
        results = self.apply_filters('older_only=')
        self.assertEqual(2, results.count())
        self.assertEqual(['alice','charlie'], [x.name for x in results])

    def test_lt_filter(self):
        results = self.apply_filters('younger_only=')
        self.assertEqual(1, results.count())
        self.assertEqual(['bob'], [x.name for x in results])

    def test_lt_filter_alphabetical(self):
        results = self.apply_filters('early_name=')
        self.assertEqual(2, results.count())
        self.assertEqual(['alice', 'bob'], [x.name for x in results])

    def test_ascending_order(self):
        results = self.apply_filters('alphabetical=')
        self.assertEqual(3, results.count())
        self.assertEqual(['alice', 'bob', 'charlie'], [x.name for x in results])

    def test_descending_order(self):
        results = self.apply_filters('reverse_alphabetical=')
        self.assertEqual(3, results.count())
        self.assertEqual(['charlie', 'bob', 'alice'], [x.name for x in results])

    def test_name_exact_alice(self):
        results = self.apply_filters('name_exact=alice')
        self.assertEqual(1, results.count())
        self.assertEqual(['alice'], [x.name for x in results])

    def test_name_exact_bob(self):
        results = self.apply_filters('name_exact=bob')
        self.assertEqual(1, results.count())
        self.assertEqual(['bob'], [x.name for x in results])

    def test_missing_key(self):
        # when presented with invalid filter names, ignore them
        results = self.apply_filters('foo=&bar=')
        self.assertEqual(3, results.count())


class ParameterizedFilterTest(FilterTest):

    def test_name_exact_charlie(self):
        results = self.apply_filters('name_exact=charlie')
        self.assertEqual(1, results.count())
        self.assertEqual(['charlie'], [x.name for x in results])
