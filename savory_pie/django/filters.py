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

    def __init__(self, fields, order_by=None):
        self.fields = fields
        self._order_by = order_by

    def filter_by(self, attribute, type, ops, published_property=None):
        pass   # TODO

    def order_by(self, attribute, published_property=None):
        pass   # TODO

    def default_order_by(self, attribute, desc=False):
        pass   # TODO

    def filter(self, ctx, params, queryset):
        # ignore ctx and params
        return queryset.filter(**self.fields)

    def describe(self, ctx, schema_dict):
        schema_dict.update(self.fields)

