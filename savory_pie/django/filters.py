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

    def __init__(self, name, fields, order_by=None):
        self.name = name
        self.fields = fields
        self._order_by = [] if order_by is None else order_by

    def __repr__(self):
        return '<' + self.__class__.__name__ + ': ' + self.name + '>'

    def filter(self, ctx, params, queryset):
        queryset = queryset.filter(**self.fields)
        if self._order_by is not None:
            queryset = queryset.order_by(*self._order_by)
        return queryset

    def describe(self, ctx, schema_dict):
        schema_dict.update(self.fields)

