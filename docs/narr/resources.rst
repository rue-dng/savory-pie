.. index::
   single: Resources

.. _narr_resources:

Using Resources
=======================================

One of the most basic things you will want to do is create a Resource.
A savory-pie Resource object defines some some way to access a piece of data or view.

Types of Resources
=======================================

... APIResource: Defines a url path to the module or api endpoint0
... ModelResrouce: A Resource that is linked to a djano ORM model
... QuerySetResource: Defines a way to query a django resource
... SchemaResource: Defines the django model schema

Resource
===============
    If object for defining resources_path it should be done on construction of the resource otherwise the resource might not be addressable

ModelResource
===============
    Defines a set of fields that are linked to model objects.

QuerySetResource
===============
    Defines a set of filters to to query the model resources.  By default it allows the querying by pk (primary key).

APIResource
===============
    Defines an endpoint, contains a set of registered endpoints.

The following Resource would allow you to use the http GET for method for the User resource at path ```users\my_user```
using the pk as a GET parameter

**Example Resource**;

.. code-block:: python

    class UserResource(ModelResource):
        resource_path = 'my_user'
        model_class = models.User

        fields = [
            fields.AttributeField('username', type=str),
            fields.AttributeField('email', type=str),
        ]

    class BoutiquePreviewSortQuerySetResource(QuerySetResource):
        resource_class = UserResource

    # Creates an APIResource
    api = APIResource('users')
    api.register_class(UserResource)
