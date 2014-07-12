.. _django_views_module:

:mod:`savory_pie.django.views`
------------------------------

:mod:`savory_pie.django.views`
==============================

.. automodule:: savory_pie.django.views

    .. autofunction:: api_view
        Example:
            added to urls.py
            url(r'^api/version1/(.*)$', api_view(api2_root_resource)))
            OR
            url(r'^api/version1/(.*)$', login_required(api_view(api2_root_resource))))


        Parameters:
            ``root_resource`` -- :`~savory_pie.resources.APIResource`
                The endpoint that exposes the apis.

    .. autofunction:: batch_api_view
        Example:
            added to urls.py
            url(r'^api/version1/batch/', batch_api_view(api2_root_resource, r'^api/version1/(?P<base_resource>.*)$')))
            OR
            url(r'^api/version1/batch/', login_required(batch_api_view(api2_root_resource, r'^api/version1/(?P<base_resource>.*)$'))))


        Parameters:
            ``root_resource`` -- :`~savory_pie.resources.APIResource`
                The endpoint that exposes the apis.

            ``base_regex`` -- :`regex`
                The regex to sub-resources, used to parse the inbound urls and rout to the given resource
