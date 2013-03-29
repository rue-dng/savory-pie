.. _formaters_modile:

:mod:`savory_pie.filters`
----------------------------

Filter protocol
==================

.. class:: Filter

    .. attribute:: content_type

        Content type this formatter supports.

        Example values would be:

        - application/json
        - application/xml

    .. method:: convert_to_public_property(bare_attribute)

        Used to convert a python style name to an exported style name. Useful
        if you like javascript style names in a json api.

        Parameters:
            ``bare_attribute``
                string name of the attribute to convert

    .. method:: to_python_value(type_, api_value)

        Converts a serialized value to a python value.

        Parameters:
            ``type_``
                callable that can turn strings in to python objects

            ``api_value``
                value that was returned in a dict by :meth:`~Filter.read_from`

        For example a json formatter would receive api_value as any json type
        (str, int, etc). A xml formater would only receive str.

    .. method:: to_api_value(type_, python_value)

        Converts a python object to a value the seraliazation format supports.

        Parameters:
            ``type_``
                callable that can turn strings in to python objects

            ``python_value``
                value that was read from a python object by a :class:`~Field`

        For example a json formatter could return any json type (int, str,
        etc), but a XML formater could only return str.

    .. method:: read_from(request)

        Creates a new dict from from the request. The values will be
        post-converted by to_python_value.

        Parameters:
            ``request``
                readable file like object

        For example a json formatter could use :func:`~json.load`. A XML
        formatter would need to parse the xml in to nexted dicts.

    .. method: write_to(body_dict, response)

        Writes the contents of body_dict to response. The values will be
        pre-converted by to_api_value.

        Parameters:
            ``body_dict``
                dict pre-converted by to_api_value

            ``response``
                write file like object

        For example a json formatter could use :func:`!json.dump`. A XML
        formatter would need to walk the nested dicts and write a XML document.

.. :mod:`savory_pie.filters`
.. ============================

.. .. automodule:: savory_pie.filters

..     .. autoclass:: JSONFilter
