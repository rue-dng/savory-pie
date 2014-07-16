import unittest
import decimal
import datetime
import pytz

import savory_pie.formatters


class JSONToAPITest(unittest.TestCase):

    def setUp(self):
        self.json_formatter = savory_pie.formatters.JSONFormatter()
        self.now = datetime.datetime(2013, 3, 5, 14, 50, 39, 123456, pytz.UTC)
        self.json_now = '2013-03-05T14:50:39.123456+00:00'

        # date
        self.now_date = datetime.date(2013, 3, 5)
        self.json_now_date = '2013-03-05'

    def test_int(self):
        result = self.json_formatter.to_api_value(int, 15)
        self.assertEqual(15, result)

    def test_long(self):
        result = self.json_formatter.to_api_value(long, 15L)
        self.assertEqual(15L, result)

    def test_float(self):
        result = self.json_formatter.to_api_value(float, 15.5)
        self.assertEqual(15.5, result)

    def test_dict(self):
        result = self.json_formatter.to_api_value(dict, {'a': 1, 'b': 2})
        self.assertEqual({'a': 1, 'b': 2}, result)

    def test_list(self):
        result = self.json_formatter.to_api_value(list, [1, 2, 3])
        self.assertEqual([1, 2, 3], result)

    def test_bool(self):
        result = self.json_formatter.to_api_value(bool, True)
        self.assertEqual(True, result)

    def test_str(self):
        result = self.json_formatter.to_api_value(str, 'abc')
        self.assertEqual('abc', result)

    def test_unicode(self):
        result = self.json_formatter.to_api_value(unicode, u'abc\U0001F4A9')
        self.assertEqual(u'abc\U0001F4A9', result)

    def test_none(self):
        result = self.json_formatter.to_api_value(unicode, None)
        self.assertEqual(None, result)

    def test_decimal(self):
        result = self.json_formatter.to_api_value(decimal.Decimal, decimal.Decimal('5.10'))
        self.assertEqual('5.10', result)

    def test_datetime(self):
        result = self.json_formatter.to_api_value(datetime.datetime, self.now)
        self.assertEqual(self.json_now, result)

    def test_date(self):
        result = self.json_formatter.to_api_value(datetime.date, self.now_date)
        self.assertEqual(self.json_now_date, result)

    def test_empty_datetime(self):
        result = self.json_formatter.to_api_value(datetime.datetime, None)
        self.assertEqual(None, result)

    def test_empty_date(self):
        result = self.json_formatter.to_api_value(datetime.date, None)
        self.assertEqual(None, result)


class JSONToPython(unittest.TestCase):

    def setUp(self):
        self.json_formatter = savory_pie.formatters.JSONFormatter()
        self.now = datetime.datetime(2013, 3, 5, 14, 50, 39, 123456, pytz.UTC)
        self.json_now = '2013-03-05T14:50:39.123456+00:00'
        self.json_now_alternative = '2013-03-05T14:50:39.123456Z'

        # date
        self.now_date = datetime.date(2013, 3, 5)
        self.json_now_date = '2013-03-05'

    def test_int(self):
        result = self.json_formatter.to_python_value(int, 15)
        self.assertEqual(15, result)

    def test_long(self):
        result = self.json_formatter.to_python_value(long, 15)
        self.assertEqual(15L, result)

    def test_float(self):
        result = self.json_formatter.to_python_value(float, 15.5)
        self.assertEqual(15.5, result)

    def test_dict(self):
        result = self.json_formatter.to_python_value(dict, {'a': 1, 'b': 2})
        self.assertEqual({'a': 1, 'b': 2}, result)

    def test_list(self):
        result = self.json_formatter.to_python_value(list, [1, 2, 3])
        self.assertEqual([1, 2, 3], result)

    def test_bool(self):
        result = self.json_formatter.to_python_value(bool, True)
        self.assertEqual(True, result)

    def test_str(self):
        result = self.json_formatter.to_python_value(str, 'abc')
        self.assertEqual('abc', result)

    def test_unicode(self):
        result = self.json_formatter.to_python_value(unicode, u'abc\U0001F4A9')
        self.assertEqual(u'abc\U0001F4A9', result)

    def test_none(self):
        result = self.json_formatter.to_python_value(unicode, None)
        self.assertEqual(None, result)

    def test_decimal(self):
        result = self.json_formatter.to_python_value(decimal.Decimal, '5.10')
        self.assertEqual(decimal.Decimal('5.10'), result)

    def test_more_decimal(self):
        for x in ['15.5', '1.550000e1', '0.000155e5', '1550e-2',
                  '1550000000000000000.0e-017',
                  '0.000000000000000155e+017']:
            result = self.json_formatter.to_python_value(decimal.Decimal, x)
            self.assertEqual(15.5, result)

    def test_datetime(self):
        result = self.json_formatter.to_python_value(datetime.datetime, self.json_now)
        self.assertEqual(self.now, result)

    def test_datetime_alternative(self):
        result = self.json_formatter.to_python_value(datetime.datetime, self.json_now_alternative)
        self.assertEqual(self.now, result)

    def test_none_datetime(self):
        result = self.json_formatter.to_python_value(datetime.datetime, None)
        self.assertEqual(None, result)

    def test_crazy_datetimes(self):
        for craziness in ('', False, {}, [], 3.14159, 3 + 4j,
                          'Rumplestiltskin', self, (3 + 4j).conjugate):
            try:
                self.json_formatter.to_python_value(datetime.datetime, craziness)
                self.fail(repr(craziness) + ' should not be parsable as a datetime')
            except TypeError:
                pass

    def test_date(self):
        result = self.json_formatter.to_python_value(datetime.date, self.json_now_date)
        self.assertEqual(self.now_date, result)

    def test_none_date(self):
        result = self.json_formatter.to_python_value(datetime.date, None)
        self.assertEqual(None, result)

    def test_unparsable_data(self):
        # should raise a TypeError
        # The following datatypes can parse any string as legal data so we don't try
        # to test them here: list, bool, str, unicode.
        unparsable = 'unparsable_data'
        for _type, svalue in [(int, unparsable),
                              (long, unparsable),
                              (float, unparsable),
                              (dict, unparsable),
                              (type(None), unparsable),
                              (datetime.datetime, unparsable)]:
            message = ('Expected a TypeError for unparsable ' + str(_type)
                       + ' with value ' + repr(svalue))
            succeeded_incorrectly = False
            try:
                self.json_formatter.to_python_value(_type, svalue)
                succeeded_incorrectly = True
            except TypeError:
                pass
            except Exception, e:
                self.fail(message + ', got ' + str(e.__class__))
            if succeeded_incorrectly:
                self.fail(message)
