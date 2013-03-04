.. _django_resources_module:

:mod:`savory_pie.django.resources`
----------------------------------

.. automodule:: savory_pie.django.resources

    .. autoclass:: QuerySetResource

        Attributes:
            .. attribute:: resource_class

                type of Resource to create for a given Model in the queryset

            .. autoattribute:: page_size

    .. autoclass:: ModelResource

        Attributes:
            .. attribute:: model_class

                type of Model consumed / create by this Resource.

            .. autoattribute:: fields

            .. autoattribute:: parent_resource_path

            .. autoattribute:: published_key
