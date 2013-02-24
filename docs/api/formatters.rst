.. _formaters_modile:

:mod:`savory_pie.formatters`
----------------------------

Formatter protocol
==================

.. class:: Formatter

    .. attribute:: content_type

        Content type this formatter supports.

        - application/json
        - application/xml

    .. method:: default_published_property(bare_attribute)

        Used to convert a python style name to an exported style name. Useful
        if you like javascript style names in a json api.

        bare_attribute - string name of the attribute to convert

    .. method:: to_python_value(type_, api_value)

        Converts a serialized value to a python value.

        - For json formatters the api_value could be a str, int etc.
        - For xml formatters the api_value would always be a str.

    .. method:: to_api_value(type_, python_value)

        Converts a python object to a value the seraliazation format supports.

        - For json formatters the you could return int, str etc.
        - For xml formatters the you could only return str.

    .. method:: read_from(request)

        Creates a new dict from from the request. The values will be
        post-converted by to_python_value.

        - For json loads
        - For xml read attributes or child nodes

        request - readable file like object

    .. method: write_to(body_dict, response)

        Writes the contents of body_dict to response. The values will be
        pre-converted by to_api_value.

        - For json dumps
        - For xml write attributes or child nodes

        body_dict - dict pre-converted by to_api_value
        response - writeable file like object

:mod:`savory_pie.formatters`
============================

.. automodule:: savory_pie.formatters

    .. autoclass:: JSONFormatter
