from mock import Mock
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
import random

class QuerySet(object):
    def __init__(self, *elements, **kwargs):
        #if not elements:
        #    raise ValueError, 'model_class required if no elements are provided'
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
    class DoesNotExist(ObjectDoesNotExist):
        pass

    objects = Manager()

    def __init__(self, **kwargs):
        super(Model, self).__init__()
        self.pk = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)

        def save_side_effect():
            if self.pk is None:
                self.pk = random.randint(1000, 10000)

        self.save = Mock(name='save', side_effect=save_side_effect)
        self.delete = Mock(name='delete')


# Not quite exactly semantically equivalent to Django because an empty QuerySet
# will have queryset.model resolve to Model rather than the specified sub-class;
# however, this is close enough for testing purposes.
Model.objects.all = Mock(return_value=QuerySet(model_class=Model))