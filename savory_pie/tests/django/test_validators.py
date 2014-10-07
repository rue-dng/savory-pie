import pytz
import unittest
from datetime import datetime, timedelta

import django
from django.db import models

from savory_pie import fields as base_fields
from savory_pie.django import resources, fields
from savory_pie.tests.mock_context import mock_context
from savory_pie.django.validators import (
    ValidationError,
    validate,
    ResourceValidator,
    DatetimeFieldSequenceValidator,
    RequiredTogetherValidator,
    FieldValidator,
    StringFieldZipcodeValidator,
    StringFieldExactMatchValidator,
    StringFieldMaxLengthValidator,
    IntFieldMinValidator,
    IntFieldMaxValidator,
    IntFieldRangeValidator,
    DatetimeFieldMinValidator,
    DatetimeFieldMaxValidator,
)


now = datetime.now().replace(tzinfo=pytz.utc)
long_ago = now - timedelta(hours=10)
ancient = long_ago - timedelta(hours=1)
later = now + timedelta(hours=1)
too_late = later + timedelta(hours=1)
ridiculous = too_late + timedelta(hours=1)

model_save_attempted = False


class NonSavingModel(models.Model):
    def save(self, *args, **kwargs):
        global model_save_attempted
        model_save_attempted = True


class Car(NonSavingModel):
    make = models.CharField(max_length=20)
    year = models.IntegerField()
    ugly = models.BooleanField()
    mileage = models.DecimalField()

    def to_json(self):
        return {
            'make': self.make,
            'year': self.year,
            'ugly': self.ugly
        }


class BugOnWindshield(NonSavingModel):
    car = models.ForeignKey(Car, related_name='bugs')
    color = models.CharField(max_length=20)


class User(models.Model):
    name = models.CharField(max_length=20)
    age = models.IntegerField()
    before = models.DateTimeField()
    after = models.DateTimeField()
    systolic_bp = models.IntegerField()
    vehicle = models.ForeignKey(Car)
    stolen_vehicle = models.ForeignKey(Car)


class CarIsStolenValidator(ResourceValidator):

    error_message = 'The car should not be stolen.'

    def check_value(self, model):
        return False


class CarNotUglyValidator(ResourceValidator):

    error_message = 'The car should not be ugly.'

    def check_value(self, model):
        return not model['ugly']


class IntFieldPrimeValidator(FieldValidator):

    json_name = 'prime_number'

    error_message = 'This should be a prime number.'

    def __init__(self, maxprime):
        self._primes = _primes = [2, 3, 5, 7]

        def test_prime(x, _primes=_primes):
            for p in _primes:
                if p * p > x:
                    return True
                if (x % p) == 0:
                    return False
        for x in range(11, maxprime + 1, 2):
            if test_prime(x):
                _primes.append(x)
        self.populate_schema()

    def check_value(self, value):
        return value in self._primes


class BugOnWindshieldResource(resources.ModelResource):
    parent_resource_path = 'bug'
    model_class = BugOnWindshield
    fields = [
        fields.AttributeField(attribute='color', type=str),
        fields.ReverseField('car')
    ]


class BugValidator(FieldValidator):
    '''
    This is a validator on a ``RelatedManagerField``. We are validating a list of
    subresources embedded in a containing resource. Since we might need to look
    at the source_dict for the containing resource to perform a correct validation,
    it is provided to the ``find_errors`` method in the ``parent_dict`` attribute
    of the last argument, which would otherwise just be a list of source_dicts for
    the subresources. All the normal list behaviors are still available.
    '''

    json_name = 'no_green_bugs_on_new_cars'   # other color bugs are OK

    error_message = 'New cars should not have green bugs on the windshield.'

    def find_errors(self, error_dict, ctx, key, resource, field, source_dict_list):
        car_year = source_dict_list.parent_dict['year']
        green_bugs = filter(lambda bug: bug['color'] == 'green', source_dict_list)
        if car_year >= 2013 and len(green_bugs) > 0:
            self._add_error(error_dict, key, self.error_message)


class CarTestResource(resources.ModelResource):
    parent_resource_path = 'cars'
    model_class = Car

    validators = [
        CarNotUglyValidator()
    ]

    fields = [
        fields.AttributeField(
            attribute='make',
            type=str,
            validator=StringFieldExactMatchValidator(
                'Toyota', error_message='why is he not driving a Toyota?'
            )
        ),
        fields.AttributeField(
            attribute='year',
            type=int,
            validator=IntFieldMinValidator(
                2010, error_message='car is too old'
            )
        ),
        fields.RelatedManagerField(
            attribute='bugs',
            resource_class=BugOnWindshieldResource,
            validator=BugValidator()
        )
    ]


class RequiredCarTestResource(resources.ModelResource):
    parent_resource_path = 'cars'
    model_class = Car

    fields = [
        fields.AttributeField(attribute='make', type=str),
        fields.AttributeField(attribute='year', type=int),
    ]

    validators = [
        RequiredTogetherValidator(
            'make',
            'year',
            null=True,
            error_message=u'Make and year are required if either is provided.'
        ),
    ]


# ALWAYS fail validation
class StolenCarTestResource(resources.ModelResource):
    parent_resource_path = 'stolencars'
    model_class = Car

    validators = [
        CarIsStolenValidator()
    ]

    fields = [
        fields.AttributeField(attribute='make', type=str),
        fields.AttributeField(attribute='year', type=int)
    ]


class UserTestResource(resources.ModelResource):
    parent_resource_path = 'users'
    model_class = User

    validators = [
        DatetimeFieldSequenceValidator('before', 'after')
    ]

    fields = [
        fields.AttributeField(
            attribute='name',
            type=str,
            validator=StringFieldExactMatchValidator('Bob')
        ),
        fields.AttributeField(
            attribute='age',
            type=int,
            validator=(
                IntFieldMinValidator(21, error_message='too young to drink'),
                IntFieldPrimeValidator(100)
            )
        ),
        fields.AttributeField(
            attribute='before',
            type=datetime,
            validator=DatetimeFieldMinValidator(
                long_ago,
                error_message='keep it recent',
            )
        ),
        fields.AttributeField(
            attribute='after',
            type=datetime,
            validator=DatetimeFieldMaxValidator(
                too_late,
                error_message='do not be late'
            )
        ),
        fields.AttributeField(
            attribute='systolic_bp',
            type=int,
            validator=IntFieldRangeValidator(
                100,
                120,
                error_message='blood pressure out of range'
            )
        ),
        fields.SubModelResourceField('vehicle', CarTestResource),
        fields.SubModelResourceField('stolen_vehicle', StolenCarTestResource, skip_validation=True),
    ]


def create_car(make, year, ugly=False):
    model = Car()
    model.make = make
    model.year = year
    model.ugly = ugly
    return model


def validate_user_resource(name, age, start, end, systolic, car=None, stolen_car=None):
    source_dict = dict(name=name, age=str(age), before=start.isoformat(), after=end.isoformat(),
                       systolicBp=int(systolic), vehicle=(car and car.to_json()),
                       stolenVehicle=(stolen_car and stolen_car.to_json()))
    return validate(mock_context(), 'user', UserTestResource(User()), source_dict)


class ValidationTestCase(unittest.TestCase):

    maxDiff = None


class NoOpField(object):
    def handle_incoming(self, ctx, source_dict, target_obj):
        pass

    def handle_outgoing(self, ctx, source_obj, target_dict):
        pass


class OptionalValidationTestCase(ValidationTestCase):

    class OptionalResource(UserTestResource):
        validators = []

        fields = [
            NoOpField()
        ]

    def test_optional_validation(self):
        """
        Resources and Fields should not be required to have validation
        """
        model = User()
        resource = self.OptionalResource(model)
        errors = validate(mock_context(), 'user', resource, {})
        self.assertEqual({}, errors)


class SimpleValidationTestCase(ValidationTestCase):

    def test_okay(self):
        errors = validate_user_resource('Bob', 23, now, later, 120)
        self.assertEqual({}, errors)

    def test_not_recent(self):
        errors = validate_user_resource('Bob', 23, ancient, long_ago, 120)
        self.assertEqual({'user.before': ['keep it recent']}, errors)

    def test_not_late(self):
        errors = validate_user_resource('Bob', 23, now, ridiculous, 120)
        self.assertEqual({'user.after': ['do not be late']}, errors)

    def test_dates_out_of_order(self):
        errors = validate_user_resource('Bob', 23, later, now, 120)
        self.assertEqual(
            {'user':
                ['Datetimes are not in expected sequence.']},
            errors)

    def test_bogus_decimal(self):
        model = Car()
        model.make = 'Toyota'
        model.year = 2010
        model.ugly = False
        resource = CarTestResource(model)
        with self.assertRaises(ValidationError):
            resource.put(mock_context(), {
                'make': 'Toyota',
                'year': '2010',
                'ugly': 'False',
                'mileage': '123abc'
            })

    def test_wrong_name(self):
        errors = validate_user_resource('Jack', 23, now, later, 120)
        self.assertEqual(
            {'user.name':
                ['This should exactly match the expected value.']},
            errors)

    def test_too_young(self):
        errors = validate_user_resource('Bob', 19, now, later, 120)
        self.assertEqual(
            {'user.age':
                ['too young to drink']},
            errors)

    def test_prime_age(self):
        errors = validate_user_resource('Bob', 24, now, later, 120)
        self.assertEqual(
            {'user.age':
                ['This should be a prime number.']},
            errors)

    def test_hypertensive(self):
        errors = validate_user_resource('Bob', 23, now, later, 140)
        self.assertEqual(
            {'user.systolicBp':
                ['blood pressure out of range']},
            errors)

    def test_hypotensive(self):
        errors = validate_user_resource('Bob', 23, now, later, 80)
        self.assertEqual(
            {'user.systolicBp':
                ['blood pressure out of range']},
            errors)

    def test_perfect_storm(self):
        errors = validate_user_resource('Jack', 18, later, now, 140)
        self.assertEqual(
            {'user':
                ['Datetimes are not in expected sequence.'],
             'user.age':
                ['too young to drink', 'This should be a prime number.'],
             'user.name':
                ['This should exactly match the expected value.'],
             'user.systolicBp':
                ['blood pressure out of range']},
            errors)

    def test_required_together_validator(self):
        resource = RequiredCarTestResource(Car())

        good = validate(mock_context(), 'RequiredTogether', resource, {})
        self.assertEqual(good, {})

        bad = validate(mock_context(), 'RequiredTogether', resource, {'make': 'Tesla'})
        self.assertEqual(bad, {'RequiredTogether': [u'Make and year are required if either is provided.']})

        bad = validate(mock_context(), 'RequiredTogether', resource, {'year': 2012})
        self.assertEqual(bad, {'RequiredTogether': [u'Make and year are required if either is provided.']})


class SubModelValidationTestCase(ValidationTestCase):

    def test_okay(self):
        car = create_car('Toyota', 2011)
        errors = validate_user_resource('Bob', 23, now, later, 120, car)
        self.assertEqual({}, errors)

    def test_ugly(self):
        car = create_car('Toyota', 2011, ugly=True)
        errors = validate_user_resource('Bob', 23, now, later, 120, car)
        self.assertEqual({'user.vehicle': ['The car should not be ugly.']}, errors)

    def test_wrong_make(self):
        car = create_car('Honda', 2012)
        errors = validate_user_resource('Bob', 23, now, later, 120, car)
        self.assertEqual({'user.vehicle.make': ['why is he not driving a Toyota?']}, errors)

    def test_too_old(self):
        car = create_car('Toyota', 2008)
        errors = validate_user_resource('Bob', 23, now, later, 120, car)
        self.assertEqual({'user.vehicle.year': ['car is too old']}, errors)

    def test_skip_validation(self):
        stolen_car = create_car('Toyota', 2011)
        errors = validate_user_resource('Bob', 23, now, later, 120, stolen_car=stolen_car)
        self.assertEqual({}, errors)


class RelatedManagerFieldValidationTestCase(ValidationTestCase):

    def setUp(self):
        # Because of the app loading refactoring introduced in Django 1.7, this step is necessary
        # See https://docs.djangoproject.com/en/dev/releases/1.7/#app-loading-refactor
        try:
            django.setup()
        except AttributeError:
            pass

        global model_save_attempted
        self.ctx = mock_context()
        self.model = Car()
        self.resource = CarTestResource(self.model)
        self.ctx.peek.return_value = self.model
        model_save_attempted = False

    def test_old_car_with_zero_bugs(self):
        self.resource.put(self.ctx, {
            'make': 'Toyota',
            'year': 2010,
            'ugly': False,
            'bugs': []
        })
        self.assertTrue(model_save_attempted)

    def test_old_car_with_green_bugs(self):
        self.resource.put(self.ctx, {
            'make': 'Toyota',
            'year': 2010,
            'ugly': False,
            'bugs': [
                {'color': 'green'},
                {'color': 'red'},
                {'color': 'green'},
                {'color': 'yellow'},
                {'color': 'green'}
            ]
        })
        self.assertTrue(model_save_attempted)

    def test_old_car_with_non_green_bugs(self):
        self.resource.put(self.ctx, {
            'make': 'Toyota',
            'year': 2010,
            'ugly': False,
            'bugs': [
                {'color': 'red'},
                {'color': 'yellow'},
                {'color': 'blue'}
            ]
        })
        self.assertTrue(model_save_attempted)

    def test_new_car_with_zero_bugs(self):
        self.resource.put(self.ctx, {
            'make': 'Toyota',
            'year': 2013,
            'ugly': False,
            'bugs': []
        })
        self.assertTrue(model_save_attempted)

    def test_new_car_with_green_bugs(self):
        with self.assertRaises(ValidationError):
            self.resource.put(self.ctx, {
                'make': 'Toyota',
                'year': 2013,
                'ugly': False,
                'bugs': [
                    {'color': 'green'},
                    {'color': 'red'},
                    {'color': 'green'},
                    {'color': 'yellow'},
                    {'color': 'green'}
                ]
            })
        self.assertFalse(model_save_attempted)

    def test_new_car_with_non_green_bugs(self):
        self.resource.put(self.ctx, {
            'make': 'Toyota',
            'year': 2013,
            'ugly': False,
            'bugs': [
                {'color': 'red'},
                {'color': 'yellow'},
                {'color': 'blue'}
            ]
        })
        self.assertTrue(model_save_attempted)


class SchemaGetTestCase(ValidationTestCase):

    def test_validation_schema_get(self):
        resource = resources.SchemaResource(UserTestResource)
        ctx = mock_context()
        ctx.build_resource_uri = lambda resource: 'uri://users/schema/'
        result = resource.get(ctx)
        self.assertEqual(
            [{
                'text': 'Datetimes are not in expected sequence.',
                'fields': 'before,after',
                'name': 'dates_in_sequence'
            }],
            result['validators']
        )
        for field_name in result['fields']:
            field = result['fields'][field_name]
            validators = field['validators']
            self.assertTrue(type(validators) is list)
            [self.assertTrue(type(v) is dict) for v in validators]
            expected = {
                'after': [{'name': 'datetime_max',
                           'text': 'do not be late',
                           'max': too_late.isoformat()}],
                'age': [{'name': 'int_min',
                         'text': 'too young to drink',
                         'min': 21},
                        {'name': 'prime_number',
                         'text': 'This should be a prime number.'}],
                'before': [{'name': 'datetime_min',
                            'text': 'keep it recent',
                            'min': long_ago.isoformat()}],
                'name': [{'expected': 'Bob',
                          'name': 'exact_string',
                          'text': 'This should exactly match the expected value.'}],
                'systolicBp': [{'max': 120,
                                'min': 100,
                                'name': 'int_range',
                                'text': 'blood pressure out of range'}],
                'vehicle': [],
                'stolenVehicle': []
            }
            self.assertEqual(expected[field_name], validators)


class KnownValidatorsTester(ValidationTestCase):

    def test_datetime_field_sequence_validator(self):
        ctx = mock_context()
        v = DatetimeFieldSequenceValidator('a', 'b', 'c')
        badness = {'foo': ['Datetimes are not in expected sequence.']}
        for (first, second, third, expected) in (
            (now, later, too_late, {}),
            (later, now, too_late, badness),
            (now, too_late, later, badness),
            (too_late, later, now, badness)
        ):
            error_dict = {}
            v.find_errors(error_dict, ctx, 'foo', None, {'a': first.isoformat(),
                                                         'b': second.isoformat(),
                                                         'c': third.isoformat()})
            self.assertEqual(expected, error_dict)

    def test_string_field_zipcode_validator(self):
        ctx = mock_context()
        v = StringFieldZipcodeValidator()
        field = base_fields.Field()
        field._attribute = 'bar'
        field._type = str
        badness = {'foo.bar': ['This should be a zipcode.']}
        for (value, expected) in (
            ('02134', {}),
            ('01701', {}),
            ('01701-7627', {}),
            ('90210', {}),
            ('65536', {}),
            ('01234567890', badness),
            ('01234-567890', badness),
        ):
            error_dict = {}
            v.find_errors(error_dict, ctx, 'foo', None, field, value)
            self.assertEqual(expected, error_dict)

    def test_string_field_exact_match_validator(self):
        ctx = mock_context()
        v = StringFieldExactMatchValidator('01701-7627')
        field = base_fields.Field()
        field._attribute = 'bar'
        field._type = str
        badness = {'foo.bar': ['This should exactly match the expected value.']}
        for (value, expected) in (
            ('01701-7627', {}),
            ('02134', badness),
            ('01701', badness),
            ('90210', badness),
            ('65536', badness),
            ('01234567890', badness),
            ('01234-567890', badness),
        ):
            error_dict = {}
            v.find_errors(error_dict, ctx, 'foo', None, field, value)
            self.assertEqual(expected, error_dict)

    def test_string_field_max_length_validator(self):
        ctx = mock_context()
        v = StringFieldMaxLengthValidator(80)
        field = base_fields.Field()
        field._attribute = 'bar'
        field._type = str
        badness = {'foo.bar': ['This should not exceed the expected string length.']}
        for (value, expected) in (
            ('A', {}),
            (5 * 'A', {}),
            (10 * 'A', {}),
            (40 * 'A', {}),
            (79 * 'A', {}),
            (80 * 'A', {}),
            (81 * 'A', badness),
            (85 * 'A', badness),
            (100 * 'A', badness),
            (200 * 'A', badness),
            (500 * 'A', badness),
        ):
            error_dict = {}
            v.find_errors(error_dict, ctx, 'foo', None, field, value)
            self.assertEqual(expected, error_dict)

    def test_int_field_min_validator(self):
        ctx = mock_context()
        v = IntFieldMinValidator(11)
        field = base_fields.Field()
        field._attribute = 'bar'
        field._type = int
        badness = {'foo.bar': ['This value should be greater than or equal to the minimum.']}
        for (value, expected) in (
            ('0', badness),
            ('5', badness),
            ('11', {}),
            ('23', {}),
            ('90210', {})
        ):
            error_dict = {}
            v.find_errors(error_dict, ctx, 'foo', None, field, value)
            self.assertEqual(expected, error_dict)

    def test_int_field_max_validator(self):
        ctx = mock_context()
        v = IntFieldMaxValidator(11)
        field = base_fields.Field()
        field._attribute = 'bar'
        field._type = int
        badness = {'foo.bar': ['This value should be less than or equal to the maximum.']}
        for (value, expected) in (
            ('0', {}),
            ('5', {}),
            ('11', {}),
            ('23', badness),
            ('90210', badness)
        ):
            error_dict = {}
            v.find_errors(error_dict, ctx, 'foo', None, field, value)
            self.assertEqual(expected, error_dict)

    def test_int_field_range_validator(self):
        ctx = mock_context()
        v = IntFieldRangeValidator(4, 11)
        field = base_fields.Field()
        field._attribute = 'bar'
        field._type = int
        badness = {'foo.bar': ['This value should be within the allowed integer range.']}
        for (value, expected) in (
            ('0', badness),
            ('3', badness),
            ('4', {}),
            ('5', {}),
            ('10', {}),
            ('11', {}),
            ('12', badness),
            ('23', badness),
            ('90210', badness)
        ):
            error_dict = {}
            v.find_errors(error_dict, ctx, 'foo', None, field, value)
            self.assertEqual(expected, error_dict)

    def test_datetime_field_min_validator(self):
        ctx = mock_context()
        v = DatetimeFieldMinValidator(now)
        field = base_fields.Field()
        field._attribute = 'bar'
        field._type = datetime
        badness = {'foo.bar': ['This value should be no earlier than the minimum datetime.']}
        for (value, expected) in (
            (ancient, badness),
            (long_ago, badness),
            (now, {}),
            (later, {}),
            (too_late, {})
        ):
            error_dict = {}
            v.find_errors(error_dict, ctx, 'foo', None, field, value.isoformat())
            self.assertEqual(expected, error_dict)

    def test_datetime_field_max_validator(self):
        ctx = mock_context()
        v = DatetimeFieldMaxValidator(now)
        field = base_fields.Field()
        field._attribute = 'bar'
        field._type = datetime
        badness = {'foo.bar': ['This value should be no later than the maximum datetime.']}
        for (value, expected) in (
            (ancient, {}),
            (long_ago, {}),
            (now, {}),
            (later, badness),
            (too_late, badness)
        ):
            error_dict = {}
            v.find_errors(error_dict, ctx, 'foo', None, field, value.isoformat())
            self.assertEqual(expected, error_dict)
