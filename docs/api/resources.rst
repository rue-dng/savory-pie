.. _resources_module:

:mod:`savory_pie.resources`
---------------------------

Resource protocol
=================

.. class:: Resource

    Attributes:

        .. attribute:: resource_path

            Internal path (from root of the resource tree to this Resource).  If
            not set, this is auto-filled during Resource traversal; however, if you
            wish for a Resource to always be addressable, resource_path should be
            set at construction.

        .. attribute:: allowed_methods

            List of HTTP methods that this resource allows

            .. code::

                allowed_methods = ['GET', 'POST]

    .. method:: get_child_resource(ctx, path_fragment)

        Parameters:

            ``ctx`` -- :class:`~savory_pie.context.APIContext`
                The context of this API call

            ``path_fragment``
                Part of the URI after being split on /

        Return the next child resource or None

    .. method:: get(ctx, \**kwargs)

        Optional method that is called during a GET request.

        Parameters:

            ``ctx`` -- :class:`~savory_pie.context.APIContext`
                The context of this API call

            ``kwargs``
                Dict of query prams

        get is provided an :class:`~savory_pie.context.APIContext` and an optional set of kwargs that include the
        query string params.

        Returns a dict of data to be serialized to the requested format.

    .. method:: post(ctx, dict)

        Optional method that is called during a POST request.

        Parameters:

            ``ctx`` -- :class:`~savory_pie.context.APIContext`
                The context of this API call

            ``dict``
                 deserialized representation of the body content

        Returns a new Resource

    .. method:: put(ctx, dict)

        Optional method that is called during a PUT request.

        Parameters:

            ``ctx`` -- :class:`~savory_pie.context.APIContext`
                The context of this API call

            ``dict``
                 deserialized representation of the body content

    .. method:: delete(ctx)

        Parameters:

            ``ctx`` -- :class:`~savory_pie.context.APIContext`
                The context of this API call

        Optional method that is called during a DELETE request.

:mod:`savory_pie.resources`
===========================

.. automodule:: savory_pie.resources

    .. autoclass:: Resource

        Attributes:
            .. autoattribute:: resource_path

            .. autoattribute:: allowed_methods

    .. autoclass:: APIResource
        :members:

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
