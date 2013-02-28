#protocol QuerySetFilter:
#   def filter(self, ctx, params, queryset)
    """
    Filters (or orders) the queryset according to the specified criteria
    """
#   def describe(self, ctx, schema_dict)
    """
    Fills in schema_dict with information about the set of valid filtering
    criteria.
    """

class StandardFilter(object):
    def __init__(self, fields, order_by=None):
        pass

    def filter_by(self, attribute, type, ops, published_property=None):
        pass

    def order_by(self, attribute, published_property=None):
        pass

    def default_order_by(self, attribute, desc=False):
        pass

    def filter(self, ctx, params, queryset):
        pass

    def describe(self, ctx, schema_dict):
        pass

