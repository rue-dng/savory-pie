from mock import Mock
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
import random

class QuerySet(object):
    def __init__(self, *elements):
        if elements:
            self.model = type(elements[0])
        else:
            self.model = Model

        self._elements = elements
        self._selected = set()
        self._prefetched = set()

    def __iter__(self):
        return iter(self._elements)

    def count(self):
        return len(self._elements)

    def filter(self, **kwargs):
        queryset = QuerySet(*self._filter_elements(**kwargs))
        queryset._selected = set(queryset._selected)
        queryset._prefetched = set(queryset._prefetched)
        return queryset

    def get(self, **kwargs):
        filtered_elements = self._filter_elements(**kwargs)
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

    def _filter_elements(self, **kwargs):
        filtered_elements = self._elements
        for attr, value in kwargs.iteritems():
            filtered_elements = \
                [element for element in self._elements if getattr(element, attr) == value]
        return filtered_elements


class Manager(Mock):
    def __init__(self):
        super(Manager, self).__init__(spec=[])

    def all(self):
        return QuerySet()

class Model(Mock):
    class DoesNotExist(ObjectDoesNotExist):
        pass

    objects = Manager()

    def __init__(self, **kwargs):
        super(Model, self).__init__(spec=[])
        self.pk = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)

        def save_side_effect():
            if self.pk is None:
                self.pk = random.randint(1000, 10000)

        self.save = Mock(name='save', side_effect=save_side_effect)
        self.delete = Mock(name='delete')