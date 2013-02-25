.. _index:

Welcome to Savory Pie's documentation!
======================================

Savory Pie is an API building library, we give you the pieces to build the API
you need. Currently Django is the main target, but the only dependencies on
Django are a single view and Resources and Fields that understand Django's ORM.

A Basic API might look something like this:

.. code-block:: python

   class UserResource(savory_pie.resources.ModelResource):
       parent_resource_path = 'users'
       model_class = User

        fields = [
            fields.PropertyField(property='name', type=str),
            fields.PropertyField(property='age', type=int)
        ]


    class UserQuerySetResource(savory_pie.resources.QuerySetResource):
        resource_path = 'users'
        resource_class = UserResource

In urls.py :

.. code-block:: python

    api_resource = resources.APIResource()
    api_resource.register_class(UserQuerySetResource)

    url(r'^api/v1/(.*)$', savory_pie.views.api_view(api_resource))

Narrative documentation
=======================
.. toctree::
   :maxdepth: 2

   narr/getting_started
   narr/resources
   narr/fields
   narr/extending

API Documentation
=================

Documentation for all of Savory Pie API.

.. toctree::
   :maxdepth: 2

   api

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

