import datetime
import re
import string

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

    dateRegex = re.compile('(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})')

    def __init__(self, name, criteria, order_by=None):
        self.name = name
        self.criteria = criteria or {}
        self._order_by = order_by or []

    def __repr__(self):
        return '<' + self.__class__.__name__ + ': ' + self.name + '>'

    def get_param_value(self, name, params, criteria):
        pass

    def filter(self, ctx, params, queryset):
        name = ctx.formatter.convert_to_public_property(self.name)
        if name in params._GET:
            criteria = self.criteria.copy()
            self.get_param_value(name, params, criteria)
            limit = None
            # Django just uses 'limit' for this but there might be legitimate uses
            # in models for a field called 'limit', so use a more specific name.
            if criteria.has_key('limit_object_count'):
                limit = criteria.pop('limit_object_count')
            queryset = queryset.filter(**criteria)
            if self._order_by is not None:
                queryset = queryset.order_by(*self._order_by)
            if limit:
                queryset = queryset[:limit]
        return queryset

    def describe(self, ctx, schema_dict):
        schema_dict['filtering'] = self.criteria
        schema_dict['ordering'] = self._order_by


class ParameterizedFilter(StandardFilter):

    def __init__(self, name, paramkey, criteria=None, order_by=None):
        self.name = name
        self.paramkey = paramkey
        self.criteria = criteria or {}
        self._order_by = order_by or []

    def get_param_value(self, name, params, criteria):
        value = params._GET.get(name)
        m = self.dateRegex.match(value)
        if m is not None:
            year, month, date, hour, minute, second = \
                map(string.atoi, [m.group(i) for i in range(1, 7)])
            value = datetime.datetime(year, month, date, hour, minute, second)
        else:
            try:
                value = float(value)
            except ValueError:
                try:
                    value = int(value)
                except ValueError:
                    pass
        criteria[self.paramkey] = value
