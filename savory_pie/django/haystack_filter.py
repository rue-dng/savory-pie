from savory_pie.django.filters import ParameterizedFilter
from haystack.query import SearchQuerySet


class HaystackFilter(ParameterizedFilter):
    """
    Assuming Haystack is available as a way to search models, use a Haystack search instead
    of a Django filter operation. The filter parameter is treated as a Haystack search term.
    Any additional search criteria, or the order_by stuff, is subsequently treated normally.
    """

    def __init__(self, name, criteria=None, order_by=None):
        ParameterizedFilter.__init__(self, name, name, criteria, order_by)

    def filter(self, ctx, params, queryset):
        name = self.is_applicable(ctx, params)
        if name:
            value = self.get_param_value(name, ctx, params)
            queryset = SearchQuerySet().filter(content=str(value)).models(queryset.model)
            queryset = self.apply(self.criteria, queryset)
        return queryset
