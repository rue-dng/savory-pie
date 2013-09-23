import collections
import datetime
import re
import savory_pie


class ValidationError(Exception):
    def __init__(self, resource, errors):
        self.resource = resource
        self.errors = errors


def validate(ctx, key, resource, source_dict):
    """
    Descend through a resource, including its fields and any related resources
    or submodels, looking for validation errors in any resources or models whose
    validators flag issues with content therein.

    Parameters:

        ``ctx``

        ``key``
            the current path fragment of the dictionary key which will be used to store
            any errors found in the returned dict -- in the initial call to validate,
            this should probably be the name of the class being validated e.g. "user"

        ``resource``
            the ModelResource instance whose data is to be validated

        ``source_dict``

    Returns:

        a dict mapping dotted keys (representing resources or fields) to
        validation errors

    """
    key = ctx.formatter.convert_to_public_property(key)
    error_dict = {}
    if source_dict and resource:
        if hasattr(resource, 'fields') and \
           isinstance(resource.fields, collections.Iterable):
            for field in resource.fields:
                if not hasattr(field, 'name'):
                    continue

                fieldname = ctx.formatter.convert_to_public_property(field.name)
                if fieldname in source_dict:
                    value = source_dict[fieldname]
                    if isinstance(value, list):
                        # RelatedManagerField validator might want to examine parent dict
                        class SourceDictList(list):
                            def __init__(self, source_dicts, parent_dict):
                                self[:] = source_dicts
                                self.parent_dict = parent_dict

                        value = SourceDictList(value, source_dict)

                    # ignore validation if value hasn't changed
                    if hasattr(resource, 'model'):
                        try:
                            orig_value = getattr(resource.model, field.name, None)
                            if orig_value == ctx.formatter.to_python_value(type(orig_value), value):
                                continue
                        except Exception:
                            pass

                    # attempt to validate field
                    if hasattr(field, 'validator') and field.validator:
                        if isinstance(field.validator, collections.Iterable):
                            for validator in field.validator:
                                validator.find_errors(error_dict, ctx, key, resource, field, value)
                        else:
                            field.validator.find_errors(error_dict, ctx, key, resource, field, value)
                    if hasattr(field, 'validate_resource'):
                        error_dict.update(field.validate_resource(ctx, key, resource, value))

        if hasattr(resource, 'validators') and \
           isinstance(resource.validators, collections.Iterable):
            for validator in resource.validators:
                validator.find_errors(error_dict, ctx, key, resource, source_dict)
    return error_dict


class BaseValidator(object):

    """
    Validators are used to determine that the values of model fields are acceptable
    according to programmatically specifiable criteria::

        class ValidationTestResource(resources.ModelResource):
            parent_resource_path = 'users'
            model_class = User

            validators = [
                DatetimeFieldSequenceValidator('start_date', 'end_date')
            ]

            fields = [
                fields.AttributeField(attribute='name', type=str,
                    validator=StringFieldExactMatchValidator('Bob')),
                fields.AttributeField(attribute='age', type=int,
                    validator=(IntFieldMinValidator(21, 'too young to drink'),
                               IntFieldPrimeValidator(100))),
                    # A field can take either a single validator,
                    # or a list or tuple of multiple validators.
                fields.AttributeField(attribute='before', type=datetime),
                fields.AttributeField(attribute='after', type=datetime),
                fields.AttributeField(attribute='systolic_bp', type=int,
                    validator=IntFieldRangeValidator(100, 120,
                        'blood pressure out of range')),
            ]


    When you apply *BaseValidator.validate* to an instance of ValidationTestResource,
    it will check to see if all the criteria are satisfied, and will return a dict giving
    all violations as key-value pairs, where the keys are dotted Python names for the
    model or field in question, and the values are lists of error messages. So if several
    criteria fail to be met, you might see something like this::

        {
            'savory_pie.tests.django.test_validators.ValidationTestResource':
                ['Datetimes are not in expected sequence.'],
            'savory_pie.tests.django.test_validators.ValidationTestResource.age':
                ['too young to drink',
                 'This should be a prime number.'],
            'savory_pie.tests.django.test_validators.ValidationTestResource.name':
                ['This should exactly match the expected value.'],
            'savory_pie.tests.django.test_validators.ValidationTestResource.systolic_bp':
                ['blood pressure out of range']
        }

    You can write your own validators, like *IntFieldPrimeValidator* above::

        class IntFieldPrimeValidator(FieldValidator):

            error_message = 'This should be a prime number.'

            def __init__(self, maxprime):
                self._primes = _primes = [2, 3, 5, 7]
                def test_prime(x, _primes=_primes):
                    for p in _primes:
                        if p * p > x:
                            return True
                        if (x %% p) == 0:
                            return False
                for x in range(11, maxprime + 1, 2):
                    if test_prime(x):
                        _primes.append(x)

            def check_value(self, value):
                return value in self._primes

    As a general rule, a validator has a *find_errors* method which makes calls to the
    *check_value* method, and if errors are found, they are stored in a dict, keyed by
    the dotted name of the non-compliant model or field.

    """

    error_message = 'Validation failure message goes here'
    """
    The error message should give a clear description of the nature of the validation
    failure, if one occurs.
    """

    json_name = 'What the front end calls this validator'
    """
    This should be a name understood by the front-end developers as referring to this
    particular validator so that they can wire up JavaScript to validate HTML forms in
    the browser.
    """

    null = False
    """
    Ignore null values for any fields which should be validated.
    """

    def __init__(self, *args, **kwargs):
        self.error_message = kwargs.pop('error_message', self.error_message)
        self.null = kwargs.pop('null', False)
        self.populate_schema(**kwargs)

    def _add_error(self, error_dict, key, error):
        if key in error_dict:
            error_dict[key].append(error)
        else:
            error_dict[key] = [error]

    def populate_schema(self, **kwargs):
        """
        Every validator *MUST* call this method in its constructor. The *kwargs*
        should be name-value pairs for any parameters required for validation. If the
        constructor sets error_message, that should happen *before* the call to this
        method.
        """
        self._schema = schema = {
            'name': self.json_name,
            'text': self.error_message
        }
        for key, value in kwargs.items():
            schema[key] = value

    def to_schema(self):
        """
        Subclasses are expected to overload this method with a string used in
        the front end for HTML form validation, for example in the context of
        something like `jQuery-Validation-Engine`_.

        .. _`jQuery-Validation-Engine`: https://github.com/posabsolute/jQuery-Validation-Engine

        Returns:

            a string representing the constraints on this resource or field, in a form
            that's useful on the front end, e.g. JavaScript
        """
        return self._schema

    def check_value(self, value):
        """
        Extend this method to test whatever needs testing on a model or field. Return
        True if the value is OK, False if it's unacceptable.
        """
        return False


########## Resource validators ###########


class ResourceValidator(BaseValidator):

    """
    Base class for validators that apply to ModelResource instances. These will usually
    look at relationships between field values, as the fields themselves will be
    individually validated.
    """

    def find_errors(self, error_dict, ctx, key, resource, source_dict):
        """
        Search for validation errors in the database model underlying a resource.
        """
        if not self.check_value(source_dict):
            self._add_error(error_dict, key, self.error_message)


class DatetimeFieldSequenceValidator(ResourceValidator):

    """
    Test an AttributeField of type 'int' to make sure it falls within a given
    range (inclusive at both ends).

    Parameters:

        ``*date_fields``
            a list of names of AttributeFields of type 'datetime' which are
            required to be in chronological sequence

        ``error_message``
            optional: the message to appear in the error dictionary if this
            condition is not met
    """

    json_name = 'dates_in_sequence'

    error_message = 'Datetimes are not in expected sequence.'

    def __init__(self, *args, **kwargs):
        kwargs['fields'] = ','.join(args)
        super(DatetimeFieldSequenceValidator, self).__init__(**kwargs)
        self._date_fields = args

    def find_errors(self, error_dict, ctx, key, resource, source_dict):
        """
        Verify that specified datetime fields exist, and are in chronological sequence
        as expected.
        """
        values = []
        for attr in self._date_fields:
            public_attr = ctx.formatter.convert_to_public_property(attr)
            if self.null and source_dict.get(public_attr) is None:
                return
            elif public_attr not in source_dict:
                self._add_error(error_dict, key,
                                'Cannot find datetime field "' + attr + '"')
                return
            values.append(ctx.formatter.to_python_value(datetime.datetime,
                                                        source_dict[public_attr]))
        for before, after in zip(values[:-1], values[1:]):
            if before > after:
                self._add_error(error_dict, key, self.error_message)
                return


class RequiredFieldValidator(ResourceValidator):
    """
    Ensure that a particular field of a resource exists.

    Parameters:

        ``field``
            the name of the required field

        ``error_message``
            optional: the message to appear in the error dictionary if this
            condition is not met
    """

    json_name = 'required_field'

    error_message = 'This field is required'

    def __init__(self, field, *args, **kwargs):
        self.field = field
        super(RequiredFieldValidator, self).__init__(**kwargs)

    def find_errors(self, error_dict, ctx, key, resource, source_dict):
        json_key = ctx.formatter.convert_to_public_property(self.field)
        if not source_dict.get(json_key):
            self._add_error(error_dict, key, self.error_message + ': ' + json_key)


class RequiredTogetherValidator(ResourceValidator):
    """
    Test a tuple of fields to ensure that if a value for one field in the set is
    provided, that all fields in the set have values provided.

    Parameters:

        ``*fields``
            a list of names of savory_pie Fields, which as a set is required if a
            value for any single field is provided

        ``error_message``
            optional: the message to appear in the error dictionary if this
            condition is not met
    """

    json_name = 'required_together'

    error_message = 'This set of fields is required if any one is provided.'

    def __init__(self, *args, **kwargs):
        kwargs['fields'] = ','.join(args)
        super(RequiredTogetherValidator, self).__init__(**kwargs)
        self._fields = args

    def find_errors(self, error_dict, ctx, key, resource, source_dict):
        values = {}
        for attr in self._fields:
            public_attr = ctx.formatter.convert_to_public_property(attr)
            if not self.null and public_attr not in source_dict:
                self._add_error(error_dict, key, 'Cannot find field "' + attr + '"')
                return
            values[attr] = source_dict.get(public_attr)

        missing = False
        required = False
        for value in values.values():
            if value is None:
                missing = True
            else:
                required = True
        if required and missing:
            self._add_error(error_dict, key, self.error_message)


class UniqueTogetherValidator(ResourceValidator):
    """
    Test a tuple of fields to ensure their proposed values represent a unique set
    within the database. This validator is similar to Django ORM's 'unique together'
    constraint, but differs in that it accepts only a single level of fields:
        https://docs.djangoproject.com/en/dev/ref/models/options/#unique-together

    Parameters:

        ``*fields``
            a list of names of savory_pie Fields, which as a set should be unique

        ``error_message``
            optional: the message to appear in the error dictionary if this
            condition is not met
    """

    json_name = 'unique_together'

    error_message = 'This set of fields must be unique.'

    def __init__(self, *args, **kwargs):
        kwargs['fields'] = ','.join(args)
        super(UniqueTogetherValidator, self).__init__(**kwargs)
        self._fields = args

    def find_errors(self, error_dict, ctx, key, resource, source_dict):
        filters = []
        for attr in self._fields:
            public_attr = ctx.formatter.convert_to_public_property(attr)
            if self.null and source_dict.get(public_attr) is None:
                return
            elif public_attr not in source_dict:
                self._add_error(error_dict, key, 'Cannot find field "' + attr + '"')
                return

            for field in resource.fields:
                if attr == getattr(field, 'name', None):
                    try:
                        if field.__class__ == savory_pie.django.fields.SubModelResourceField:
                            if 'resourceUri' in source_dict[public_attr]:
                                pk = source_dict[public_attr]['resourceUri'].split('/')[-1]
                                filters.append({'{}__pk'.format(attr): pk})
                            elif 'name' in source_dict[public_attr]:
                                filters.append({'{}__name'.format(attr): source_dict[public_attr]['name']})
                            else:
                                #TODO allow lookup by fields other than id/name?
                                return
                        elif issubclass(field.__class__, savory_pie.django.fields.AttributeField):
                            filters.append({attr: source_dict[public_attr]})
                    except Exception:
                        pass

        if filters and hasattr(resource, 'model'):
            try:
                qset = resource.model.__class__.objects.all()
                for f in filters:
                    qset = qset.filter(**f)
                if len(qset):
                    # if validation fails because we're re-saving an existing object, ignore
                    if len(qset) == 1 and resource.model.pk and qset[0].pk == resource.model.pk:
                        return
                    self._add_error(error_dict, key, self.error_message)
            except Exception:
                pass


class UniquePairedFieldValidator(ResourceValidator):
    """
    Test a pair of fields (a, b), such that for a given a, only one b can exist. However,
    this _unique_ combination of fields can exist unlimited times.

    Parameters:

        ``*fields``
            a pair of savory_pie Fields (a, b), such that for a given a,
            only one b can exist

        ``error_message``
            optional: the message to appear in the error dictionary if this
            condition is not met
    """

    json_name = 'unique_paired_field'

    error_message = 'First field is already present in another pair.'

    def __init__(self, *args, **kwargs):
        kwargs['fields'] = ','.join(args)
        super(UniquePairedFieldValidator, self).__init__(**kwargs)
        self._fields = args

    def find_errors(self, error_dict, ctx, key, resource, source_dict):
        filters = []
        for attr in self._fields:
            public_attr = ctx.formatter.convert_to_public_property(attr)
            if self.null and source_dict.get(public_attr) is None:
                return
            elif public_attr not in source_dict:
                self._add_error(error_dict, key, 'Cannot find field "' + attr + '"')
                return

            for field in resource.fields:
                if attr == getattr(field, 'name', None):
                    try:
                        if field.__class__ == savory_pie.django.fields.SubModelResourceField:
                            if 'resourceUri' in source_dict[public_attr]:
                                pk = source_dict[public_attr]['resourceUri'].split('/')[-1]
                                filters.append({'{}__pk'.format(attr): pk})
                            elif 'name' in source_dict[public_attr]:
                                filters.append({'{}__name'.format(attr): source_dict[public_attr]['name']})
                            else:
                                #TODO allow lookup by fields other than id/name?
                                return
                        elif issubclass(field.__class__, savory_pie.django.fields.AttributeField):
                            filters.append({attr: source_dict[public_attr]})
                    except Exception:
                        pass

        if filters and hasattr(resource, 'model'):
            try:
                qset = resource.model.__class__.objects.filter(**filters[0]).exclude(**filters[1])
                if len(qset):
                    self._add_error(error_dict, key, self.error_message)
            except Exception:
                pass


########## Field validators ############


class FieldValidator(BaseValidator):

    """
    Base class for all validators of fields: AttributeField, URIResourceField,
    SubObjectResourceField, IterableField
    """

    def find_errors(self, error_dict, ctx, key, resource, field, value):
        """
        Search for validation errors in a field of a database model.
        """
        fieldname = ctx.formatter.convert_to_public_property(field.name)
        value = ctx.formatter.to_python_value(field._type, value)
        if value is None:
            if self.null:
                return
            self._add_error(error_dict, key + '.' + fieldname, '{} is required'.format(fieldname))
        if not self.check_value(value):
            self._add_error(error_dict, key + '.' + fieldname, self.error_message)


class StringFieldZipcodeValidator(FieldValidator):

    """
    Test an AttributeField of type 'str' to make sure it's a valid zipcode.

    **TODO**:

        Handle international postal codes, some are six digits???
    """

    json_name = 'us_zipcode'

    error_message = 'This should be a zipcode.'

    pattern = re.compile(r'^\d{5}(-\d{4})?$')

    def check_value(self, value):
        """
        Verify that the value is a five-digit string.

        """
        try:
            return self.pattern.match(value)
        except TypeError:
            return False


class StringFieldExactMatchValidator(FieldValidator):

    """
    Test an AttributeField of type 'str' to make sure it exactly matches an
    expected value.

    Parameters:

        ``expected``
            the case-sensitive string value that we expect to see

        ``error_message``
            optional: the message to appear in the error dictionary if this
            condition is not met
    """

    json_name = 'exact_string'

    error_message = 'This should exactly match the expected value.'

    def __init__(self, expected, **kwargs):
        kwargs['expected'] = expected
        super(StringFieldExactMatchValidator, self).__init__(**kwargs)
        self._expected = expected

    def check_value(self, value):
        """
        Verify that the value is a string exactly matching the constructor argument.
        """
        return value == self._expected


class StringFieldMaxLengthValidator(FieldValidator):

    """
    Test an AttributeField of type 'str' to make sure it does not exceed the
    expected length.

    Parameters:

        ``expected_length``
            the maximum length for an allowable string

        ``error_message``
            optional: the message to appear in the error dictionary if this
            condition is not met
    """

    json_name = 'string_maxlen'

    error_message = 'This should not exceed the expected string length.'

    def __init__(self, expected_length, **kwargs):
        kwargs['expected_length'] = expected_length
        super(StringFieldMaxLengthValidator, self).__init__(**kwargs)
        self._expected_length = expected_length

    def check_value(self, value):
        """
        Verify that the value is a string whose length doesn't exceed the maximum.
        """
        return ((isinstance(value, str) or isinstance(value, unicode))
                and len(value) <= self._expected_length)


class IntFieldMinValidator(FieldValidator):

    """
    Test an AttributeField of type 'int' to make sure it is no smaller than a
    specified minimum.

    Parameters:

        ``min``
            the specified minimum

        ``error_message``
            optional: the message to appear in the error dictionary if this
            condition is not met
    """

    json_name = 'int_min'

    error_message = 'This value should be greater than or equal to the minimum.'

    def __init__(self, _min, **kwargs):
        kwargs['min'] = _min
        super(IntFieldMinValidator, self).__init__(**kwargs)
        self._min = _min

    def check_value(self, intvalue):
        """
        Verify integer value is no less than specified minimum.
        """
        return type(intvalue) is int and intvalue >= self._min


class IntFieldMaxValidator(FieldValidator):

    """
    Test an AttributeField of type 'int' to make sure it is no greater than a
    specified maximum.

    Parameters:

        ``max``
            the specified maximum

        ``error_message``
            optional: the message to appear in the error dictionary if this
            condition is not met
    """

    json_name = 'int_max'

    error_message = 'This value should be less than or equal to the maximum.'

    def __init__(self, _max, **kwargs):
        kwargs['max'] = _max
        super(IntFieldMaxValidator, self).__init__(**kwargs)
        self._max = _max

    def check_value(self, intvalue):
        """
        Verify integer value is no greater than specified maximum.
        """
        return type(intvalue) is int and intvalue <= self._max


class IntFieldRangeValidator(FieldValidator):

    """
    Test an AttributeField of type 'int' to make sure it falls within a given
    range (inclusive at both ends).

    Parameters:

        ``min``
            the bottom of the range

        ``max``
            the top of the range

        ``error_message``
            optional: the message to appear in the error dictionary if this
            condition is not met
    """

    json_name = 'int_range'

    error_message = 'This value should be within the allowed integer range.'

    def __init__(self, _min, _max, **kwargs):
        kwargs.update({'min': _min, 'max': _max})
        super(IntFieldRangeValidator, self).__init__(**kwargs)
        self._min, self._max = _min, _max

    def check_value(self, intvalue):
        """
        Verify that numerical value is within specified range.
        """
        return type(intvalue) is int and intvalue >= self._min and intvalue <= self._max


class DatetimeFieldMinValidator(FieldValidator):

    """
    Test an AttributeField of type datetime to make sure it is no earlier than a
    specified minimum.

    Parameters:

        ``min``
            the specified minimum

        ``error_message``
            optional: the message to appear in the error dictionary if this
            condition is not met
    """

    json_name = 'datetime_min'

    error_message = 'This value should be no earlier than the minimum datetime.'

    def __init__(self, _min, **kwargs):
        kwargs['min'] = _min.isoformat()
        super(DatetimeFieldMinValidator, self).__init__(**kwargs)
        self._min = _min

    def check_value(self, datetimevalue):
        """
        Verify integer value is no less than specified minimum.
        """
        return type(datetimevalue) is datetime.datetime and datetimevalue >= self._min


class DatetimeFieldMaxValidator(FieldValidator):

    """
    Test an AttributeField of type datetime to make sure it is no later than a
    specified maximum.

    Parameters:

        ``max``
            the specified maximum

        ``error_message``
            optional: the message to appear in the error dictionary if this
            condition is not met
    """

    json_name = 'datetime_max'

    error_message = 'This value should be no later than the maximum datetime.'

    def __init__(self, _max, **kwargs):
        kwargs['max'] = _max.isoformat()
        super(DatetimeFieldMaxValidator, self).__init__(**kwargs)
        self._max = _max

    def check_value(self, datetimevalue):
        """
        Verify integer value is no greater than specified maximum.
        """
        return type(datetimevalue) is datetime.datetime and datetimevalue <= self._max


class DateFieldMinValidator(FieldValidator):

    """
    Test an AttributeField of type date to make sure it is no earlier than a
    specified minimum.

    Parameters:

        ``min``
            the specified minimum

        ``error_message``
            optional: the message to appear in the error dictionary if this
            condition is not met
    """

    json_name = 'date_min'

    error_message = 'This value should be no earlier than the minimum date.'

    def __init__(self, _min, **kwargs):
        kwargs['min'] = _min.isoformat()
        super(DateFieldMinValidator, self).__init__(**kwargs)
        self._min = _min

    def check_value(self, datevalue):
        """
        Verify integer value is no less than specified minimum.
        """
        return type(datevalue) is datetime.date and datevalue >= self._min
