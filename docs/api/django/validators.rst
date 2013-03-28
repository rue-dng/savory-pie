.. _django_validators_module:

:mod:`savory_pie.django.validators`
-----------------------------------

.. automodule:: savory_pie.django.validators

    .. autoclass:: BaseValidator
        :members: check_value, error_message, validate

    .. autoclass:: ResourceValidator
        :members: find_errors

    .. autoclass:: FieldValidator
        :members: find_errors

    .. autoclass:: StringFieldZipcodeValidator
        :members: check_value

    .. autoclass:: StringFieldExactMatchValidator
        :members: __init__, check_value

    .. autoclass:: IntFieldMinValidator
        :members: __init__, find_errors

    .. autoclass:: IntFieldMaxValidator
        :members: __init__, find_errors

    .. autoclass:: IntFieldRangeValidator
        :members: __init__, find_errors
