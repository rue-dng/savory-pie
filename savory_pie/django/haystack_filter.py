from savory_pie.django.filters import ParameterizedFilter
from haystack.query import SearchQuerySet


class HaystackFilter(ParameterizedFilter):
    """
    Assuming Haystack is available as a way to search models, use a Haystack search instead
    of a Django filter operation. The filter parameter is treated as a Haystack search term.
    Any additional search criteria, or the order_by stuff, is subsequently treated normally.
    """

    def __init__(self, name='q', criteria=None, order_by=None):
        ParameterizedFilter.__init__(self, name, name, criteria, order_by)

    def filter(self, ctx, params, queryset):
        name = self.is_applicable(ctx, params)
        if name:
            value = self.get_param_value(name, ctx, params)
            hs_results = SearchQuerySet().filter(content=unicode(value)).models(queryset.model)
            pks = (result.pk for result in hs_results)
            queryset = queryset.filter(pk__in=pks)
            queryset = self.apply(self.criteria, queryset)
        return queryset
