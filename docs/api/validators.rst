.. _formaters_modile:

:mod:`savory_pie.validators`
----------------------------

Validator protocol
==================

.. class:: BaseValidator

    .. method:: validate(cls, resource, key)

    .. method:: _add_error(self, error_dict, key, error)

    .. method:: to_schema(self)

    .. method:: check_value(self, value)


API
===

.. automodule:: savory_pie.django.validators

    .. autoclass:: BaseValidator
        :members: validate, _add_error, to_schema, check_value

    .. autoclass:: ResourceValidator
        :members: find_errors

    .. autoclass:: DatetimeFieldSequenceValidator
        :members: __init__, find_errors

    .. autoclass:: FieldValidator
        :members: find_errors

    .. autoclass:: StringFieldZipcodeValidator
        :members: check_value

    .. autoclass:: StringFieldExactMatchValidator
        :members: __init__, check_value

    .. autoclass:: IntFieldMinValidator
        :members: __init__, check_value

    .. autoclass:: IntFieldMaxValidator
        :members: __init__, check_value

    .. autoclass:: IntFieldRangeValidator
        :members: __init__, check_value
