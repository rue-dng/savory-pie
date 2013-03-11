import unittest
import sys
from mock import Mock, MagicMock, call
from django.http import QueryDict

from savory_pie.django import resources, fields, filters
from savory_pie.tests.django import mock_orm
from savory_pie.tests.mock_context import mock_context
from savory_pie.resources import EmptyParams


class MockUser(mock_orm.Model):
    pass

_users = mock_orm.QuerySet(
    MockUser(pk=1, name='Alice', age=31),
    MockUser(pk=2, name='Charlie', age=26),
    MockUser(pk=3, name='Bob', age=20)
)

MockUser.objects.all = Mock(return_value=_users)

_filters = [
	filters.StandardFilter('official_test_user', {'name': 'Alice'}),
	filters.StandardFilter('bogus_test_user', {'name': 'Nobody'}),
	filters.StandardFilter('early_name', {'name__lt': 'C00000'}),
	filters.StandardFilter('younger_only', {'age__lt': 25}),
	filters.StandardFilter('older_only', {'age__gt': 25}),
	filters.StandardFilter('alphabetical', {}, order_by=['name']),
	filters.StandardFilter('reverse_alphabetical', {}, order_by=['-name']),
	filters.ParameterizedFilter('name_exact', 'name'),
	]

class StandardFilterTest(unittest.TestCase):

    class Params:
        def __init__(self, *filternames):
            querystring = "&".join(filternames)
            self._GET = QueryDict(querystring)

    def apply_filters(self, *filternames):
        ctx = None
        queryset = _users
        params = self.Params(*filternames)
        for filter in _filters:
            queryset = filter.filter(ctx, params, queryset)
        return queryset

    def test_without_filtering(self):
        results = self.apply_filters()
        self.assertEqual(3, results.count())
        self.assertEqual(['Alice', 'Charlie', 'Bob'], [x.name for x in results])

    def test_good_filter(self):
        results = self.apply_filters('official_test_user=')
        self.assertEqual(1, results.count())
        self.assertEqual(['Alice'], [x.name for x in results])

    def test_bad_filter(self):
        results = self.apply_filters('bogus_test_user=')
        self.assertEqual(0, results.count())
        self.assertEqual([], [x.name for x in results])

    def test_multiple_filters(self):
        results = self.apply_filters('official_test_user=', 'early_name=')
        # older_only: Alice,Charlie,Bob -> Alice,Charlie
        # early_name: Alice,Charlie -> Alice
        self.assertEqual(1, results.count())
        self.assertEqual(['Alice'], [x.name for x in results])

    def test_gt_filter(self):
        results = self.apply_filters('older_only=')
        self.assertEqual(2, results.count())
        self.assertEqual(['Alice','Charlie'], [x.name for x in results])

    def test_lt_filter(self):
        results = self.apply_filters('younger_only=')
        self.assertEqual(1, results.count())
        self.assertEqual(['Bob'], [x.name for x in results])

    def test_lt_filter_alphabetical(self):
        results = self.apply_filters('early_name=')
        self.assertEqual(2, results.count())
        self.assertEqual(['Alice', 'Bob'], [x.name for x in results])

    def test_ascending_order(self):
        results = self.apply_filters('alphabetical=')
        self.assertEqual(3, results.count())
        self.assertEqual(['Alice', 'Bob', 'Charlie'], [x.name for x in results])

    def test_descending_order(self):
        results = self.apply_filters('reverse_alphabetical=')
        self.assertEqual(3, results.count())
        self.assertEqual(['Charlie', 'Bob', 'Alice'], [x.name for x in results])

    def test_name_exact_alice(self):
        results = self.apply_filters('name_exact=Alice')
        self.assertEqual(1, results.count())
        self.assertEqual(['Alice'], [x.name for x in results])

    def test_name_exact_bob(self):
        results = self.apply_filters('name_exact=Bob')
        self.assertEqual(1, results.count())
        self.assertEqual(['Bob'], [x.name for x in results])

    def test_name_exact_charlie(self):
        results = self.apply_filters('name_exact=Charlie')
        self.assertEqual(1, results.count())
        self.assertEqual(['Charlie'], [x.name for x in results])
