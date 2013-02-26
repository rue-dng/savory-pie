import unittest
from savory_pie.tests import mock_orm
from savory_pie.django.utils import Related

class RelatedTest(unittest.TestCase):
    def test_select(self):
        related = Related()

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
        related = Related()

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
        related = Related()
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
        related = Related()
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
        related = Related()
        sub_related = related.sub_prefetch('foo')
        sub_sub_related = sub_related.sub_select('bar')

        sub_sub_related.select('baz')

        # Because foo was prefetch, the sub-select of bar is also forced into
        # prefetch mode, so foo__bar__baz ends up being prefetched.
        self.assertEqual(related._prefetch, {
            'foo__bar__baz'
        })

    def test_empty_prepare(self):
        related = Related()

        queryset = related.prepare(mock_orm.QuerySet())

        self.assertEqual(queryset._selected, set())
        self.assertEqual(queryset._prefetched, set())

    def test_prepare(self):
        related = Related()

        related.select('foo')
        related.prefetch('bar')

        queryset = related.prepare(mock_orm.QuerySet())

        self.assertEqual(queryset._selected, {
            'foo'
        })
        self.assertEqual(queryset._prefetched, {
            'bar'
        })
