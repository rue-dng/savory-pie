from haystack.query import SearchQuerySet

from savory_pie.django.filters import ParameterizedFilter


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
            for value in self.get_param_values(name, ctx, params):
                value = unicode(value)
                hs_results = SearchQuerySet().models(queryset.model)
                for word in value.split():
                    hs_results = hs_results.filter(content=word)
                pks = [result.pk for result in hs_results]
                queryset = queryset.filter(pk__in=pks)
                queryset = self.apply(self.criteria, queryset)
        return queryset
