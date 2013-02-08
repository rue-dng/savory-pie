from mock import Mock

class QuerySet(object):
    def __init__(self, *elements):
        super(QuerySet, self).__init__()
        self.elements = elements

    def __iter__(self):
        return iter(self.elements)

    def filter(self, **kwargs):
        filtered_elements = self.elements
        for key, value in kwargs.iteritems():
            filtered_elements = self._filter(key, value)
        return QuerySet(*filtered_elements)

    def _filter(self, attr, value):
        return [element for element in self.elements if getattr(element, attr) == value]


class Manager(Mock):
    def __init__(self):
        super(Manager, self).__init__()

        self.all = Mock()
        self.all.return_value = QuerySet()


class Model(Mock):
    objects = Manager()

    def __init__(self, **kwargs):
        super(Model, self).__init__()

        for key, value in kwargs.iteritems():
            setattr(self, key, value)

        self.save = Mock()
        self.delete = Mock()
