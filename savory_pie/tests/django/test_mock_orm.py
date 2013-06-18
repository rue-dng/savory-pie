import unittest
from django.db.models import Q
from savory_pie.tests.django import mock_orm


class MockUser(mock_orm.Model):
    def __repr__(self):
        return '<MockUser name={}, age={}>'.format(self.name, self.age)


class TestMockORM(unittest.TestCase):
    def setUp(self):
        self.bob1 = MockUser(pk=1, name='Bob', age=12)
        self.bob2 = MockUser(pk=2, name='Bob', age=200)
        self.jill = MockUser(pk=3, name='Jill', age=45)
        self.not_bob = MockUser(pk=4, name='Not Bob', age=54)

        self.qs = mock_orm.QuerySet(self.bob1, self.bob2, self.jill, self.not_bob)

    def test_simple_filter(self):
        self.assertEqual(
            set([self.bob1, self.bob2]),
            set(self.qs.filter(name='Bob'))
        )

    def test_and_filter(self):
        self.assertEqual(
            set([self.bob1]),
            set(self.qs.filter(name='Bob', age__lt=145))
        )

    def test_q_and_filter(self):
        q = Q(name='Bob') & Q(age__lt=145)
        self.assertEqual(
            set([self.bob1]),
            set(self.qs.filter(q))
        )

    def test_q_or_filter(self):
        q = Q(name='Bob') | Q(age__lt=50)
        self.assertEqual(
            set([self.bob1, self.bob2, self.jill]),
            set(self.qs.filter(q))
        )

    def test_q_and_or_filter(self):
        q = Q(age__lt=100) & (Q(name='Bob') | Q(name='Jill'))
        self.assertEqual(
            set([self.bob1, self.jill]),
            set(self.qs.filter(q))
        )
