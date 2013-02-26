#protocol QuerySetFilter:
#   def filter(self, ctx, params, queryset)
#   def describe(self, ctx, schema_dict)


class StandardFilter(object):
    def __init__(self, fields, order_by=None)