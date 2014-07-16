import datetime
import unittest

from mock import Mock
import pytz

from savory_pie.django import filters
from savory_pie.tests.django import mock_orm
from savory_pie.tests.mock_context import mock_context
from savory_pie.formatters import JSONFormatter


class MockUser(mock_orm.Model):
    pass


now = datetime.datetime.now(tz=pytz.UTC).replace(microsecond=0)
hour = datetime.timedelta(hours=1)

_users = mock_orm.QuerySet(
    MockUser(pk=1, name='alice', age=31, when=now - hour),
    MockUser(pk=2, name='charlie', age=26, when=now),
    MockUser(pk=3, name='bob', age=20, when=now + hour)
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
    filters.ParameterizedFilter('before', 'when__lt'),
    filters.ParameterizedFilter('no_earlier_than', 'when__gte'),
    filters.ParameterizedFilter('names', 'name')
]


class Params():
    def __init__(self, params):
        self.params = params

    def __iter__(self):
        return iter(self.params)

    def get_list(self, name):
        value = self.params[name]
        if isinstance(value, list):
            return value
        else:
            return [value]


class FilterTest(unittest.TestCase):

    def apply_filters(self, filters):
        ctx = mock_context()
        queryset = _users
        params = Params({
            ctx.formatter.convert_to_public_property(name): value
            for name, value
            in filters.items()
        })

        for filter in _filters:
            queryset = filter.filter(ctx, params, queryset)
        return queryset


class StandardFilterTest(FilterTest):

    def test_without_filtering(self):
        results = self.apply_filters({})
        self.assertEqual(3, results.count())
        self.assertEqual(
            ['alice', 'charlie', 'bob'],
            [x.name for x in results]
        )

    def test_good_filter(self):
        results = self.apply_filters({'official_test_user': ''})
        self.assertEqual(1, results.count())
        self.assertEqual(['alice'], [x.name for x in results])

    def test_bad_filter(self):
        results = self.apply_filters({'bogus_test_user': ''})
        self.assertEqual(0, results.count())
        self.assertEqual([], [x.name for x in results])

    def test_multiple_filters(self):
        results = self.apply_filters({'official_test_user': '', 'early_name': ''})
        # older_only: alice,charlie,bob -> alice,charlie
        # early_name: alice,charlie -> alice
        self.assertEqual(1, results.count())
        self.assertEqual(['alice'], [x.name for x in results])

    def test_gt_filter(self):
        results = self.apply_filters({'older_only': ''})
        self.assertEqual(2, results.count())
        self.assertEqual(
            sorted(['alice', 'charlie']),
            sorted([x.name for x in results])
        )

    def test_lt_filter(self):
        results = self.apply_filters({'younger_only': ''})
        self.assertEqual(1, results.count())
        self.assertEqual(['bob'], [x.name for x in results])

    def test_lt_filter_alphabetical(self):
        results = self.apply_filters({'early_name': ''})
        self.assertEqual(2, results.count())
        self.assertEqual(
            sorted(['alice', 'bob']),
            sorted([x.name for x in results])
        )

    def test_ascending_order(self):
        results = self.apply_filters({'alphabetical': ''})
        self.assertEqual(3, results.count())
        self.assertEqual(
            ['alice', 'bob', 'charlie'],
            [x.name for x in results]
        )

    def test_descending_order(self):
        results = self.apply_filters({'reverse_alphabetical': ''})
        self.assertEqual(3, results.count())
        self.assertEqual(
            ['charlie', 'bob', 'alice'],
            [x.name for x in results]
        )

    def test_name_exact_alice(self):
        results = self.apply_filters({'name_exact': 'alice'})
        self.assertEqual(1, results.count())
        self.assertEqual(['alice'], [x.name for x in results])

    def test_name_exact_bob(self):
        results = self.apply_filters({'name_exact': 'bob'})
        self.assertEqual(1, results.count())
        self.assertEqual(['bob'], [x.name for x in results])

    def test_missing_key(self):
        # when presented with invalid filter names, ignore them
        results = self.apply_filters({'foo': '', 'bar': ''})
        self.assertEqual(3, results.count())


class ParameterizedFilterTest(FilterTest):

    def test_name_exact_charlie(self):
        results = self.apply_filters({'name_exact': 'charlie'})
        self.assertEqual(1, results.count())
        self.assertEqual(set(['charlie']), set([x.name for x in results]))

    def test_parameter_data_types(self):
        # get_param_value should assume unparsable data remains a string
        ctx = mock_context()
        ctx.formatter = JSONFormatter()
        foofilter = filters.ParameterizedFilter('foo', 'bar')
        params = Params({'bar': 'unparsable'})
        values = foofilter.get_param_values('bar', ctx, params)
        self.assertEquals(1, len(values))
        self.assertEqual(set(['unparsable']), set(values))
        # parsable data should be parsed as a correct type
        now = datetime.datetime.now(tz=pytz.UTC).replace(microsecond=0)
        for value, svalue in [(11, '11'),
                              (3.14159, '3.14159'),
                              (now, now.isoformat("T"))]:
            params = Params({'bar': svalue})
            othervalues = foofilter.get_param_values('bar', ctx, params)
            self.assertEqual(set([value]), set(othervalues))
            self.assertEqual(type(value), type(othervalues[0]))

    def test_before(self):
        results = self.apply_filters({'before': now.isoformat("T")})
        self.assertEqual(1, results.count())
        self.assertEqual(set(['alice']), set([x.name for x in results]))
        results = self.apply_filters({'before': (now + hour).isoformat("T")})
        self.assertEqual(2, results.count())
        self.assertEqual(set(['alice', 'charlie']), set([x.name for x in results]))
        results = self.apply_filters({'before': (now + 2 * hour).isoformat("T")})
        self.assertEqual(3, results.count())
        self.assertEqual(set(['alice', 'charlie', 'bob']), set([x.name for x in results]))

    def test_no_earlier_than(self):
        results = self.apply_filters({'no_earlier_than': now.isoformat("T")})
        self.assertEqual(2, results.count())
        self.assertEqual(set(['charlie', 'bob']), set([x.name for x in results]))
        results = self.apply_filters({'no_earlier_than': (now + hour).isoformat("T")})
        self.assertEqual(1, results.count())
        self.assertEqual(set(['bob']), set([x.name for x in results]))
        results = self.apply_filters({'no_earlier_than': (now + 2 * hour).isoformat("T")})
        self.assertEqual(0, results.count())

    def test_multiple_names(self):
        results = self.apply_filters({'names': ['charlie', 'bob']})
        self.assertEqual(2, results.count())
        self.assertEqual(set(['charlie', 'bob']), set([x.name for x in results]))
