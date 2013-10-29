.. index::
   single: Getting Started

.. _narr_getting_started:

Creating your first API with Savory Pie and Django
=======================================

This is going to be a set of steps on how to add Savory Pie to your Django application.
You are not required to use Django with Savory Pie, but for this example we are going to go through a steps of how to
setup.

For this example we are going to assume that your Django application has a set of Models: Car and Driver.

**Example Resources**:

.. code-block:: python

    class Driver(django.db.models.Model):
        name = models.CharField(max_length=128, help_text=_('name'))
        models.ForeignKey(Car, help_text=_('car'), related_name='driver')

    class Car(django.db.models.Model):
        type = models.CharField(max_length=128, help_text=_('type'))
        open_seats =  models.PositiveIntegerField(help_text=_('type'), default=3)


When you want to add a Savory Pie resource to your application it is as simple as adding the api endpoint to your urls file

Create a root resource for your new api endpoint this endpoint should be versioned

Creating a simple ModelResource
===============
...

Creating a SubModuleResource
===============
...

Creating a QuerySetResource for your the Resources
===============
...

Creating a unified Endpoint for your Module
===============
...

Adding your api endpoint to your application
===============
To add this new CarApi endpoint all you would need to do is register this api endpoint to a root url resource and then add
it to your url patterns.

**Example Adding Your Endpoint To Your Application**:

.. code-block:: python

    from django.conf.urls import patterns, url
    from savory_pie.django.views import api_view
    import car_api

    root_resource = APIResource()
    root_resource.register(car_api)

    urlpatterns = patterns(
        ...
        url(r'^api/v2/(.*)$', api_view(root_resource))
        ...
    )

Adding Authorization
===============
...
