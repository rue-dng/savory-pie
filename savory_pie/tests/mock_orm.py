from mock import Mock
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist


class QuerySet(object):
    def __init__(self, *elements):
        super(QuerySet, self).__init__()
        self.elements = elements

    def __iter__(self):
        return iter(self.elements)

    def filter(self, **kwargs):
        return QuerySet(*self._filter_elements(**kwargs))

    def get(self, **kwargs):
        filtered_elements = self._filter_elements(**kwargs)
        count = len(filtered_elements)

        if count == 0:
            # This is not really correct, should return an exception that
            # matches the specific sub-class, but this is close enough for
            # the purpose of many tests.
            raise Model.DoesNotExist
        elif count == 1:
            return filtered_elements[0]
        else:
            raise MultipleObjectsReturned

    def _filter_elements(self, **kwargs):
        filtered_elements = self.elements
        for attr, value in kwargs.iteritems():
            filtered_elements = \
                [element for element in self.elements if getattr(element, attr) == value]
        return filtered_elements


class Manager(Mock):
    def __init__(self):
        super(Manager, self).__init__()

        self.all = Mock(return_value=QuerySet())


class Model(Mock):
    # Not exactly semantically equivalent to Django, but close enough for most tests
    class DoesNotExist(ObjectDoesNotExist):
        pass

    objects = Manager()

    def __init__(self, **kwargs):
        super(Model, self).__init__()

        for key, value in kwargs.iteritems():
            setattr(self, key, value)

        def save_side_effect():
            self.pk = 314159

        self.save = Mock(name='save', side_effect=save_side_effect)
        self.delete = Mock(name='delete')
