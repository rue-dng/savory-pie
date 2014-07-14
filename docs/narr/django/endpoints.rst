.. index::
   single: Working with django endpoints

.. .. _narr_django_endpoints:

Django Installation
=======================================
Savory Pie does not require django, or django_dirty_bits, however when using the django aspects of savory pie, you must install the following modules

.. highlight:: bash
    pip install django_dirty_bits >= 0.1.3.2
    pip install Django > 1.4

Django Endpoint
=======================================
Once you defined a number of Resources and their relative paths,
you will need to hook into django's request routing mechanisms.  You do this by
registering an endoint in urls.py.

This endpoint should define the base path to all apis.  An example of such an endpoint definition
is the following

.. code-block:: python
    from savory_pie.django.views import api_view

    urlpatterns = patterns(
        '',
        url(r'^api/v1/(.*)$', api_view(root_resource))
    )

If you desire to hook into django's user authentication/authorization mechanisms you will need to define the block
 as follows

.. code-block:: python
    from django.contrib.auth.decorators import login_required
    from savory_pie.django.views import api_view

    urlpatterns = patterns(
        '',
        url(r'^api/v1/(.*)$', login_required(api_view(root_resource)))
    )



root_resource in this case is an APIResource with multiple sub resources
 which are registered through the APIResource.register method

Django Batch Endpoint
=======================================
*WARNING*: Unless you absolutely positivity need this endpoint, we recommend that you do not utilize it, since it
can be abused.  When deciding to use this endpoint you should consider the caching needs of your application.

Some times it is desirable to make multiple resource manipulations within a single request to server.
This is usually the case for batch updates, or creates.

If you find yourself in a situation when you must make bulk updates to multiple different resources and the round trips
to the server are causing the browser to time out you can utilize this batch update endpoint.

You will need to register a batch api along side your standard api you will need to define another url endpoint and
a regex that contains a back-reference to the sub-resources.


.. code-block:: python
    from savory_pie.django.views import api_view, batch_api_view

    urlpatterns = patterns(
        '',
        url(r'^api/v1/(.*)$', api_view(root_resource))
        url(r'^api/v1/batch/', batch_api_view(root_resource, r'^api/v2/(?P<base_resource>.*)$))

    )

When making requests to this endpoint your requests must be 'POST' only requests with a body in the following format:

.. code-block:: javascript
    // Request POST /api/v1/batch
    {
        data: [
            {
                method: 'get',
                uri: 'http://host:port/api/v1/car,
                body: {
                // GET Params
                    id: 23
                }
            },
            {
                method: 'put',
                uri: 'http://host:port/api/v1/car/23,
                body: {
                    name: 'lee'
                    type: 'coup'
                }
            },
            {
                method: 'post',
                uri: 'http://host:port/api/v1/car,
                body: {
                    name: 'big one'
                    type: 'truck'
                }
            },
            {...}
        ]
    }

The requests get processed in the order they are received.
The response from the previos POST could resemble the following
.. code-block:: javascript
    // Response
    {
        data: [
            {
                uri: 'http://host:port/api/v1/car,
                status: 200,
                body: {
                    name: 'general'
                    type: 'coup'
                }
            },
            {
                status: 204,
                uri: 'http://host:port/api/v1/car,
            },
            {
                status: 201,
                uri: 'http://host:port/api/v1/car,
                location: 'http://host:port/api/v1/car/24'
            },
            {...}
        ]
    }


