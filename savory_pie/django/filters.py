import datetime
from django.db.models import Q


class StandardFilter(object):
    """Filters the results from a query on a :class:`savory_pie.django.resources.QuerySetResource`.
    Each QSR defines a set of available filters for that resource. For a model :class:`Foo` with a
    datetime field *when*, we might define filters like these::

        class FooQuerySetResource(QuerySetResource):
            resource_class = FooResource

            filters = [
                filters.StandardFilter('ancient', {'when__lt': earlyDate}),
                filters.StandardFilter('modern', {'when__gte': earlyDate,
                                                  'when_lt': laterDate}),
                filters.StandardFilter('postmodern', {'when__gte': laterDate}),
                filters.StandardFilter('postmodernReverseChronological',
                                       {'when__gte': laterDate},
                                       order_by=['-when']),
                filters.ParameterizedFilter('limit', 'limit_object_count')
            ]

    The second argument of the StandardFilter constructor (*criteria*) is a dictionary
    of Django-esque `filtering criteria`_.

    .. _`filtering criteria`: https://docs.djangoproject.com/en/dev/topics/db/queries/#retrieving-specific-objects-with-filters

    Filter names should be camel-case and should start with a lowercase letter. They
    can be invoked as part of a web API by appending them to a URL. Here is an example
    of fetching the ten most recent results from the *postmodern* category, and which
    will return a JSON array of information about those ten results::

        curl http://example.com/api/foo?postmodernReverseChronological=&limit=10

    This class is extended by :class:`ParameterizedFilter`, which allows the URL to
    include a parameter (in the example above, the limit on the query size).

    .. warning::

        Use of the special parameter *limit_object_count* will disable
        pagination on if it is under the page size. Use it only for something
        like a top-ten query.

    """

    def __init__(self, name, criteria, order_by=None):
        """
        *name*: A name for invoking the filter in a URL. Should be camel-case with
        a lowercase first letter.

        *criteria*: A dictionary specifying a set of Django-style `filtering criteria`_.

        *order_by*: An optional list of model field names used to sort the query results.
        Preface the fiield name with a minus-sign to reverse the order.

        """
        self.name = name
        self.criteria = criteria or {}
        self._order_by = order_by or []

    def __unicode__(self):
        return u'<' + self.__class__.__name__ + ': ' + self.name + '>'

    def get_param_values(self, name, ctx, params):
        """
        *name*: The name of a parameter which is treated as a key in the *params* QueryDict.

        *ctx*: A context object.

        *params*: A QueryDict of key-value pairs taken from a URL, wherein values are all strings.

        *criteria*: A dictionary to be updated, assuming the value for key *name* can be found
        and successfully parsed in *params*.

        .. note::

            In *StandardFilter* this method does nothing.

        """
        pass

    def is_applicable(self, ctx, params):
        """
        A filter applies in a particular situation if its name (converted to a
        public property by the current formatter) is found among the keys in the
        params._GET querydict. If this filter is applicable, return the converted
        name, otherwise return False.
        """
        name = ctx.formatter.convert_to_public_property(self.name)
        if name in params:
            return name
        else:
            return False

    def build_queryset(self, criteria, queryset):
        if not criteria:
            return queryset

        q = None
        for key, value in criteria.items():
            if q is None:
                q = Q(**{key: value})
            else:
                q |= Q(**{key: value})

        queryset = queryset.filter(q)
        return queryset

    def apply(self, criteria, queryset):
        """
        Apply filtering and sorting criteria to a queryset, return a result queryset.
        """
        # Django just uses 'limit' for this but there might be legitimate uses
        # in models for a field called 'limit', so use a more specific name.
        limit = criteria.pop('limit_object_count', None)

        queryset = self.build_queryset(criteria, queryset)

        if self._order_by is not None:
            queryset = queryset.order_by(*self._order_by)
        if limit:
            limit = limit[0]
            queryset = queryset[:limit]
        return queryset

    def filter(self, ctx, params, queryset):
        """
        Filters (or orders) the queryset according to the specified criteria, if
        this filter is applicable.
        """
        if self.is_applicable(ctx, params):
            queryset = self.apply(self.criteria, queryset)
        return queryset

    def describe(self, ctx, schema_dict):
        """
        Fills in schema_dict with information about the set of valid filtering
        criteria.
        """
        schema_dict['filtering'] = self.criteria
        schema_dict['ordering'] = self._order_by


class ParameterizedFilter(StandardFilter):

    """This extends the :class:`StandardFilter` class, allowing the URL to
    include a parameter.

    """

    def __init__(self, name, paramkey, criteria=None, order_by=None, value_fn=None):
        """
        *name*: A name for invoking the filter in a URL. Should be camel-case with
        a lowercase first letter.

        *paramkey*: The name of a model's field (possibly extended e.g. "fieldname__lt")
        to which the value specified in the URL will be applied.

        .. note::

            There is one special name for *paramkey*, "limit_object_count", which limits
            the query to a specified number of elements. This may break pagination, so **BE CAREFUL**.

        *criteria*: A dictionary specifying a set of Django-style `filtering criteria`_.
        It expects values to be a list.

        *order_by*: An optional list of model field names used to sort the query results.
        Preface the fiield name with a minus-sign to reverse the order.

        *value_fn*: An optional callable which is passed the raw filter value from the
        querystring and which must return the value to be used in the filter.

        """
        self.name = name
        self.paramkey = paramkey
        self.criteria = criteria or {}
        self._order_by = order_by or []
        self.value_fn = value_fn

        self.datatypes = [
            # in order of decreasing specifity/complexity
            datetime.datetime,
            int,   # an int could be mistaken for a float, so try int first
            float,
        ]

    def get_param_values(self, name, ctx, params):
        """
        *name*: The name of a parameter which is treated as a key in the *params* QueryDict.
        The value of the parameter will be parsed as a Python object, and that key-value pair
        will be added to *criteria*.

        *ctx*: A context object.

        *params*: A QueryDict of key-value pairs taken from a URL, wherein values are all strings.

        *criteria*: A dictionary to be updated, assuming the values for key *name* can be found
        and successfully parsed in *params*.

        """
        values = params.get_list(name)

        def apply_value_function(value):
            if self.value_fn is not None:
                value = self.value_fn(value)

            for _type in self.datatypes:
                try:
                    # if a cast doesn't work, a TypeError will be raised
                    # and we'll go on to the next one. if none work, it
                    # remains a string.
                    value = ctx.formatter.to_python_value(_type, value)
                    break
                except TypeError:
                    continue

            return value

        return [apply_value_function(v) for v in values]

    def build_queryset(self, criteria, queryset):
        if not criteria:
            return queryset

        q = None
        for key, values in criteria.items():
            for value in values:
                if q is None:
                    q = Q(**{key: value})
                else:
                    q |= Q(**{key: value})

        queryset = queryset.filter(q)
        return queryset

    def filter(self, ctx, params, queryset):
        """
        Filters (or orders) the queryset according to the specified criteria
        """
        name = self.is_applicable(ctx, params)
        if name:
            criteria = {self.paramkey: self.get_param_values(name, ctx, params)}
            criteria.update(self.criteria)
            queryset = self.apply(criteria, queryset)
        return queryset
