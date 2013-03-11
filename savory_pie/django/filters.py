#protocol QuerySetFilter:
#   def filter(self, ctx, params, queryset)
#       """
#       Filters (or orders) the queryset according to the specified criteria
#       """
#   def describe(self, ctx, schema_dict)
#       """
#       Fills in schema_dict with information about the set of valid filtering
#       criteria.
#       """

class StandardFilter(object):

    def __init__(self, name, criteria, order_by=None):
        self.name = name
        self.paramkey = None
        self.criteria = criteria
        self._order_by = [] if order_by is None else order_by

    def __repr__(self):
        return '<' + self.__class__.__name__ + ': ' + self.name + '>'

    def filter(self, ctx, params, queryset):
        if params._GET.__contains__(self.name):
            criteria = self.criteria.copy()
            if self.paramkey is not None:
                criteria[self.paramkey] = params._GET.get(self.name)
            queryset = queryset.filter(**criteria)
            if self._order_by is not None:
                queryset = queryset.order_by(*self._order_by)
        return queryset

    def describe(self, ctx, schema_dict):
        schema_dict['filtering'] = self.criteria
        schema_dict['ordering'] = self._order_by


class ParameterizedFilter(StandardFilter):

    def __init__(self, name, paramkey, criteria={}, order_by=None):
        self.name = name
        self.paramkey = paramkey
        self.criteria = criteria
        self._order_by = [] if order_by is None else order_by
