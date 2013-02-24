.. _fields_module:

:mod:`savory_pie.fields`
------------------------

Field protocol
==============

.. class:: Field

    .. method:: handle_incoming(ctx, source_dict, target_obj)

        Called by Resource.put or post to set Model properties on target_obj
        based on information from the source_dict.

    .. method:: handle_outgoing(ctx, source_obj, target_dict)

        Called by Resource.get to set key on the target_dict based on
        information in the Model source_obj.

    .. method:: prepare(ctx, related)

         Called by ModelResource.prepare to build up a set of related select-s
         or prefetch-es.

:mod:`savory_pie.fields`
========================

.. automodule:: savory_pie.fields

    .. autoclass:: AttributeField

    .. autoclass:: URIResourceField

    .. autoclass:: SubModelResourceField

    .. autoclass:: RelatedManagerField
