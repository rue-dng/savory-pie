import operator
import random

from django.db.models import Q
from django.db.models.signals import post_init

from mock import Mock
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist


class QuerySet(Mock):
    def __init__(self, *elements):
        super(QuerySet, self).__init__()
        if elements:
            self.model = type(elements[0])
        else:
            self.model = Model

        self._elements = elements
        self._selected = set()
        self._prefetched = set()

    def __iter__(self):
        return self.iterator()

    def iterator(self):
        return iter(self._elements)

    def __list__(self):
        raise UserWarning(u'Don\'t call list; it will not take advantage of prior prefetch optimizations')

    def all(self):
        return QuerySet(*self._elements)

    def distinct(self):

        values = \
            {
                tuple(
                    # remove the methods when comparing the uniqueness of the elements
                    [i for i in obj.__dict__.items() if i[0] not in ('save', 'delete')]
                ): obj for obj in self._elements
            }.values()
        return QuerySet(*values)

    def count(self):
        return len(self._elements)

    def exists(self):
        return len(self._elements)

    def filter(self, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], Q):
            q = args[0]
        else:
            q = Q(*args, **kwargs)
        queryset = QuerySet(*self._filter_q(q))
        queryset._selected = set(queryset._selected)
        queryset._prefetched = set(queryset._prefetched)
        return queryset

    def order_by(self, *attributes):
        def compare(x, y, attributes=attributes):
            for attr in attributes:
                if attr[:1] == '-':
                    attr = attr[1:]
                    if getattr(x, attr) > getattr(y, attr):
                        return -1
                    if getattr(x, attr) < getattr(y, attr):
                        return 1
                else:
                    if getattr(x, attr) < getattr(y, attr):
                        return -1
                    if getattr(x, attr) > getattr(y, attr):
                        return 1
            return 0
        elements = list(self._elements[:])
        elements.sort(compare)
        return QuerySet(*elements)

    def get(self, **kwargs):
        filtered_elements = list(self._filter_elements(**kwargs))
        count = len(filtered_elements)

        if count == 0:
            # This is not really correct, should return an exception that
            # matches the specific sub-class, but this is close enough for
            # the purpose of many tests.
            raise self.model.DoesNotExist
        elif count == 1:
            return filtered_elements[0]
        else:
            raise MultipleObjectsReturned

    def select_related(self, *fields):
        queryset = QuerySet(*self._elements)

        if len(fields) == 0:
            # Django selects all related when called with no arguments
            # That behavior is semi-pathological, so fake some unintended relations
            queryset._selected = {'some', 'unintended', 'relations'}
        elif len(fields) == 1 and fields[0] is None:
            # emulate the clearing behavior when passed None
            queryset._selected = set()
        else:
            # Accurately, recreate Django's broken behavior:
            # https://code.djangoproject.com/ticket/16855
            queryset._selected = set(fields)

        queryset._prefetched = set(self._prefetched)
        return queryset

    def prefetch_related(self, *fields):
        queryset = QuerySet(*self._elements)
        queryset._selected = set(self._selected)

        if len(fields) == 1 and fields[0] is None:
            # emulate the clearing behavior when passed None
            queryset._prefetched = set()
        else:
            queryset._prefetched = set(self._prefetched) | set(fields)

        return queryset

    def _filter_q(self, q):
        if not q.children:
            return set(self._elements)

        if q.connector == 'AND':
            opp = operator.and_
        else:
            opp = operator.or_

        results = None
        for child in q.children:
            if isinstance(child, Q):
                r = self._filter_q(child)
            else:
                r = self._filter_elements(**dict([child]))

            if results is None:
                results = r
            else:
                results = opp(results, r)

        return set(results)

    def _filter_elements(self, **kwargs):
        filtered_elements = self._elements
        for attr, value in kwargs.iteritems():
            if attr.endswith('__lt'):
                filtered_elements =\
                    [element for element in self._elements if
                        getattr(element, attr[:-4]) < value]
            elif attr.endswith('__gt'):
                filtered_elements =\
                    [element for element in self._elements if
                        getattr(element, attr[:-4]) > value]
            elif attr.endswith('__lte'):
                filtered_elements =\
                    [element for element in self._elements if
                        getattr(element, attr[:-5]) <= value]
            elif attr.endswith('__gte'):
                filtered_elements =\
                    [element for element in self._elements if
                        getattr(element, attr[:-5]) >= value]
            elif attr.endswith('__in'):
                filtered_elements =\
                    [element for element in self._elements if
                        getattr(element, attr[:-4]) in value]
            else:
                filtered_elements =\
                    [element for element in self._elements if
                        getattr(element, attr) == value]
        return set(filtered_elements)


class Manager(Mock):
    def all(self):
        return QuerySet()

    def __iter__(self):
        return iter(self.all())


class FieldsInitType(type):
    def __new__(meta, classname, bases, dct):
        fields = dct.get('_fields', [])
        for base in bases:
            if getattr(base, '_meta', None):
                base_meta = base._meta
                base_meta.fields = fields
                base_meta.many_to_many = []
                dct['_meta'] = base_meta
                break
        return type.__new__(meta, classname, bases, dct)


class Model(object):
    class DoesNotExist(ObjectDoesNotExist):
        pass

    _models = []
    _meta = Mock()
    objects = Manager()
    __metaclass__ = FieldsInitType

    def __init__(self, **kwargs):
        self.pk = getattr(self, 'pk', None)
        self._models.append(self)

        for key, value in kwargs.iteritems():
            setattr(self, key, value)

        def save_side_effect():
            if self.pk is None:
                self.pk = random.randint(1000, 10000)

        post_init.send(sender=self.__class__, instance=self)

        self.save = Mock(name='save', side_effect=save_side_effect)
        self.delete = Mock(name='delete')
