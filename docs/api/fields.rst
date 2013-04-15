.. _fields_module:

:mod:`savory_pie.fields`
------------------------

Field protocol
==============

.. class:: Field

    .. method:: handle_incoming(ctx, source_dict, target_obj)

        Parameters:

            ``ctx`` -- :class:`~savory_pie.context.APIContext`
                The context of this API call

            ``source_dict``
                deserialized representation of the body content

            ``target_obj``
                object to update

        Called by Resource.put or post to set Model properties on target_obj
        based on information from the source_dict.

    .. method:: handle_outgoing(ctx, source_obj, target_dict)

        Parameters:

            ``ctx`` -- :class:`~savory_pie.context.APIContext`
                The context of this API call

            ``source_obj``
                object to to read from

            ``target_dict``
                deserialized representation of the response content

        Called by Resource.get to set key on the target_dict based on
        information in the Model source_obj.

    .. method:: prepare(ctx, related)

        Optional method

        Parameters:

            ``ctx`` -- :class:`~savory_pie.context.APIContext`
                The context of this API call

            ``related`` -- :class:`~savory_pie.django_utils.Related`
                Tracks related and prefetch calls

        Called by Resource.prepare to build up a set of related select-s
        or prefetch-es.

:mod:`savory_pie.fields`
========================

.. automodule:: savory_pie.fields

    .. autoclass:: AttributeField

    .. autoclass:: URIResourceField

    .. autoclass:: URIListResourceField

    .. autoclass:: SubObjectResourceField

    .. autoclass:: IterableField
