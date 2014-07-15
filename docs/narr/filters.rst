.. index::
   single: Filters

.. _narr_filters:

Using Filters
=======================================

Here's an example. We want to be able to filter the results from a query on a QuerySetResource.
Each QSR defines a set of available filters for that resource. For a model `Foo` with a datetime field *when*,
we might define filters like these::

.. code-block:: python

    class Foo(models.Model):
        when = models.DateTimeField('when')

    class FooResource(ModelResource):
        parent_resource_path = 'foos'
        model_class = Foo

        fields = [
            AttributeField(attribute='when', type=datetime),
        ]

    class FooQuerySetResource(QuerySetResource):
        resource_class = FooResource

        filters = [

            # accept any date before earlyDate
            filters.StandardFilter('ancient', {'when__lt': earlyDate}),

            # accept a range of dates from earlyDate to laterDate
            filters.StandardFilter('modern', {'when__gte': earlyDate,
                                              'when_lt': laterDate}),

            # accept any date after laterDate
            filters.StandardFilter('postmodern', {'when__gte': laterDate}),

            # accept any date after laterDate, and sort the results with later dates first
            filters.StandardFilter('postmodernReverseChronological',
                                   {'when__gte': laterDate},
                                   order_by=['-when']),

            # limit the number of results, like MySQL's LIMIT keyword
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

The *StandardizedFilter* class is extended by *ParameterizedFilter*, which allows the URL to
include a parameter (in the example above, the limit on the query size).

.. warning::

    Use of the special parameter *limit_object_count* will disable pagination on
    the Rue La La website if it is under the page size. Use it only for something
    like a top-ten query.
