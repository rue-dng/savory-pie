import unittest
from datetime import datetime, timedelta

from savory_pie import fields as base_fields
from savory_pie.django import resources, fields
from savory_pie.django import validators as spie_validators
from savory_pie.tests.mock_context import mock_context

from django.db import models


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
        spie_validators.DatetimeFieldSequenceValidator('start_date', 'end_date')
    ]

    fields = [
        fields.AttributeField(attribute='name', type=str,
            validator=spie_validators.StringFieldExactMatchValidator('Bob')),
        fields.AttributeField(attribute='age', type=int,
            validator=(spie_validators.IntFieldMinValidator(21, 'too young to drink'),
                       IntFieldPrimeValidator(100))),
        fields.AttributeField(attribute='before', type=datetime),
        fields.AttributeField(attribute='after', type=datetime),
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
    model.start_date = start
    model.end_date = end
    model.systolic_bp = systolic
    model.vehicle = car
    resource = UserTestResource(model)
    errors = spie_validators.BaseValidator.validate(resource, 'user')
    return errors


class ValidationTestCase(unittest.TestCase):

    maxDiff = None

    def setUp(self):
        self.now = datetime.now()
        self.later = self.now + timedelta(hours=1)


class SimpleValidationTestCase(ValidationTestCase):

    def test_okay(self):
        errors = validate_user_resource('Bob', 23, self.now, self.later, 120)
        self.assertEqual({}, errors)

    def test_okay_submodel(self):
        car = create_car('Toyota', 2011)
        errors = validate_user_resource('Bob', 23, self.now, self.later, 120, car)
        self.assertEqual({}, errors)

    def test_bad_submodel_ugly(self):
        car = create_car('Toyota', 2011, ugly=True)
        errors = validate_user_resource('Bob', 23, self.now, self.later, 120, car)
        self.assertEqual({'user.vehicle': ['The car should not be ugly.']}, errors)

    def test_bad_submodel_wrong_make(self):
        car = create_car('Honda', 2012)
        errors = validate_user_resource('Bob', 23, self.now, self.later, 120, car)
        self.assertEqual({'user.vehicle.make': ['why is he not driving a Toyota?']}, errors)

    def test_bad_submodel_too_old(self):
        car = create_car('Toyota', 2008)
        errors = validate_user_resource('Bob', 23, self.now, self.later, 120, car)
        self.assertEqual({'user.vehicle.year': ['car is too old']}, errors)

    def test_dates_out_of_order(self):
        errors = validate_user_resource('Bob', 23, self.later, self.now, 120)
        self.assertEqual(
            {'user':
                ['Datetimes are not in expected sequence.']},
            errors)

    def test_wrong_name(self):
        errors = validate_user_resource('Jack', 23, self.now, self.later, 120)
        self.assertEqual(
            {'user.name':
                ['This should exactly match the expected value.']},
            errors)

    def test_too_young(self):
        errors = validate_user_resource('Bob', 19, self.now, self.later, 120)
        self.assertEqual(
            {'user.age':
                ['too young to drink']},
            errors)

    def test_prime_age(self):
        errors = validate_user_resource('Bob', 24, self.now, self.later, 120)
        self.assertEqual(
            {'user.age':
                ['This should be a prime number.']},
            errors)

    def test_hypertensive(self):
        errors = validate_user_resource('Bob', 23, self.now, self.later, 140)
        self.assertEqual(
            {'user.systolic_bp':
                ['blood pressure out of range']},
            errors)

    def test_hypotensive(self):
        errors = validate_user_resource('Bob', 23, self.now, self.later, 80)
        self.assertEqual(
            {'user.systolic_bp':
                ['blood pressure out of range']},
            errors)

    def test_perfect_storm(self):
        errors = validate_user_resource('Jack', 18, self.later, self.now, 140)
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
        errors = validate_user_resource('Bob', 23, self.now, self.later, 120, car)
        self.assertEqual({}, errors)

    def test_ugly(self):
        car = create_car('Toyota', 2011, ugly=True)
        errors = validate_user_resource('Bob', 23, self.now, self.later, 120, car)
        self.assertEqual({'user.vehicle': ['The car should not be ugly.']}, errors)

    def test_wrong_make(self):
        car = create_car('Honda', 2012)
        errors = validate_user_resource('Bob', 23, self.now, self.later, 120, car)
        self.assertEqual({'user.vehicle.make': ['why is he not driving a Toyota?']}, errors)

    def test_too_old(self):
        car = create_car('Toyota', 2008)
        errors = validate_user_resource('Bob', 23, self.now, self.later, 120, car)
        self.assertEqual({'user.vehicle.year': ['car is too old']}, errors)


class SchemaGetTestCase(ValidationTestCase):

    def test_validation_schema_get(self):
        resource = resources.SchemaResource(UserTestResource)
        ctx = mock_context()
        ctx.build_resource_uri = lambda resource: 'uri://user/schema/'
        result = resource.get(ctx)
        self.assertEqual(['javascript code for data validation'], result['validators'])
        for field_name in result['fields']:
            field = result['fields'][field_name]
            validators = field['validators']
            self.assertTrue(type(validators) is list)
            [self.assertTrue(type(v) is str) for v in validators]
            expected = {
                'after': [],
                'age': ['javascript code for data validation',
                        'javascript code for data validation'],
                'before': [],
                'name': ['javascript code for data validation'],
                'systolicBp': ['javascript code for data validation'],
                'vehicle': []
            }
            self.assertEqual(expected[field_name], validators)
