import json
import unittest
from datetime import datetime, timedelta

from savory_pie import fields as base_fields
from savory_pie.django import resources, fields
from savory_pie.django import validators as spie_validators
from savory_pie.tests.mock_context import mock_context

from django.db import models

now = datetime.now().replace(microsecond=0)
long_ago = now - timedelta(hours=10)
ancient = long_ago - timedelta(hours=1)
later = now + timedelta(hours=1)
too_late = later + timedelta(hours=1)
ridiculous = too_late + timedelta(hours=1)


class User(models.Model):
    name = models.CharField(max_length=20)
    age = models.IntegerField()
    before = models.DateTimeField()
    after = models.DateTimeField()
    systolic_bp = models.IntegerField()


class Car(models.Model):
    make = models.CharField(max_length=20)
    age = models.IntegerField()
    ugly = models.BooleanField()


class CarNotUglyValidator(spie_validators.ResourceValidator):

    error_message = 'The car should not be ugly.'

    def check_value(self, model):
        return not model.ugly


class IntFieldPrimeValidator(spie_validators.FieldValidator):

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


class CarTestResource(resources.ModelResource):
    parent_resource_path = 'cars'
    model_class = Car

    validators = [
        CarNotUglyValidator()
    ]

    fields = [
        fields.AttributeField(attribute='make', type=str,
            validator=spie_validators.StringFieldExactMatchValidator('Toyota',
                'why is he not driving a Toyota?')),
        fields.AttributeField(attribute='year', type=int,
            validator=spie_validators.IntFieldMinValidator(2010, 'car is too old'))
    ]


class UserTestResource(resources.ModelResource):
    parent_resource_path = 'users'
    model_class = User

    validators = [
        spie_validators.DatetimeFieldSequenceValidator('before', 'after')
    ]

    fields = [
        fields.AttributeField(attribute='name', type=str,
            validator=spie_validators.StringFieldExactMatchValidator('Bob')),
        fields.AttributeField(attribute='age', type=int,
            validator=(spie_validators.IntFieldMinValidator(21, 'too young to drink'),
                       IntFieldPrimeValidator(100))),
        fields.AttributeField(attribute='before', type=datetime,
            validator=spie_validators.DatetimeFieldMinValidator(long_ago,
                                                                'keep it recent')),
        fields.AttributeField(attribute='after', type=datetime,
            validator=spie_validators.DatetimeFieldMaxValidator(too_late,
                                                                'do not be late')),
        fields.AttributeField(attribute='systolic_bp', type=int,
            validator=spie_validators.IntFieldRangeValidator(100, 120,
                'blood pressure out of range')),
        fields.SubModelResourceField('vehicle', CarTestResource)
    ]

def create_car(make, year, ugly=False):
    model = Car()
    model.make = make
    model.year = year
    model.ugly = ugly
    return model

def validate_user_resource(name, age, start, end, systolic, car=None):
    model = User()
    model.name = name
    model.age = age
    model.before = start
    model.after = end
    model.systolic_bp = systolic
    model.vehicle = car
    resource = UserTestResource(model)
    errors = spie_validators.BaseValidator.validate(resource, 'user')
    return errors


class ValidationTestCase(unittest.TestCase):

    maxDiff = None


class NoOpField(object):
    def handle_incoming(self, ctx, source_dict, target_obj):
        pass

    def handle_outgoing(self, ctx, source_obj, target_dict):
        pass


class OptionalValidationTestCase(ValidationTestCase):

    class OptionalResource(resources.ModelResource):
        parent_resource_path = 'users'
        model_class = User

        fields = [
            NoOpField()
        ]

    def test_optional_validation(self):
        """
        Fields should not be required to have validation
        """
        model = User()
        resource = UserTestResource(model)
        errors = spie_validators.BaseValidator.validate(resource, 'user')


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
            {'user.systolic_bp':
                ['blood pressure out of range']},
            errors)

    def test_hypotensive(self):
        errors = validate_user_resource('Bob', 23, now, later, 80)
        self.assertEqual(
            {'user.systolic_bp':
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
             'user.systolic_bp':
                ['blood pressure out of range']},
            errors)


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


class SchemaGetTestCase(ValidationTestCase):

    def test_validation_schema_get(self):
        resource = resources.SchemaResource(UserTestResource)
        ctx = mock_context()
        ctx.build_resource_uri = lambda resource: 'uri://user/schema/'
        result = resource.get(ctx)
        # import sys, pprint; pprint.pprint(result, stream=sys.stderr)
        self.assertEqual([{
                             'text': 'Datetimes are not in expected sequence.',
                             'fields': 'before,after',
                             'name': 'dates_in_sequence'
                         }],
                         result['validators'])
        for field_name in result['fields']:
            field = result['fields'][field_name]
            validators = field['validators']
            self.assertTrue(type(validators) is list)
            [self.assertTrue(type(v) is dict) for v in validators]
            expected = {
                'after': [{'name': 'datetime_max',
                           'text': 'do not be late',
                           'value': too_late.isoformat()}],
                'age': [{'name': 'int_min',
                         'text': 'too young to drink',
                         'value': 21},
                        {'name': 'prime_number',
                         'text': 'This should be a prime number.'}],
                'before': [{'name': 'datetime_min',
                            'text': 'keep it recent',
                            'value': long_ago.isoformat()}],
                'name': [{'expected': 'Bob',
                          'name': 'exact_string',
                          'text': 'This should exactly match the expected value.'}],
                'systolicBp': [{'max': 120,
                                'min': 100,
                                'name': 'int_range',
                                'text': 'blood pressure out of range'}],
                'vehicle': []
            }
            self.assertEqual(expected[field_name], validators)
