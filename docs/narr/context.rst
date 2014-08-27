.. _filters_modile:

:mod:`savory_pie.context`
----------------------------

Context protocol
=====================

This is the Context of the request made to the api.  It contains headers, request object, and resource locations.


.. class:: APIContext

   .. method:: set_expiration_header(new_expiration)
        Parameters:

              ``new_expiration`` -- :class:`~datetime.datetime`

          Saves the min expiration date on the APIContext to be serialized into the headers oh headers call.
