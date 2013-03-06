import unittest
import decimal
import datetime
import time
from mock import Mock

import savory_pie.formatters


class JSONToAPITest(unittest.TestCase):

    def setUp(self):
        self.json_formatter = savory_pie.formatters.JSONFormatter()

    def test_int(self):
        result = self.json_formatter.to_api_value(int, 15)
        self.assertEqual(15, result)

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


class JSONDatesDecimals(unittest.TestCase):

    def setUp(self):
        self.json_formatter = savory_pie.formatters.JSONFormatter()
        self.now = datetime.datetime(2013, 3, 5, 14, 50, 39)
        self.json_now = '2013-03-05T14:50:39'

    def test_read_decimals(self):
        for x in ['15.5', '1.550000e1', '0.000155e5', '1550e-2',
                  '1550000000000000000.0e-017',
                  '0.000000000000000155e+017']:
            mock = Mock()
            mock.read = lambda: x
            result = self.json_formatter.read_from(mock)
            self.assertEqual(15.5, result)
            self.assertEqual(15.5, self.json_formatter.to_python_value(float, x))

    def test_write_dates(self):
        mock = Mock()
        self.json_formatter.write_to(self.now, mock)
        write_args = tuple(mock.mock_calls[0])[1]
        self.assertEqual('"' + self.json_now + '"', write_args[0])
        self.assertEqual(self.json_now,
                         self.json_formatter.to_api_value(datetime.datetime,
                                                          self.now))

    def test_read_dates(self):
        mock = Mock()
        mock.read = lambda: self.json_now
        self.assertEqual(self.now, self.json_formatter.read_from(mock))
        self.assertEqual(self.now,
                         self.json_formatter.to_python_value(datetime.datetime,
                                                             self.json_now))


class JSONToPython(unittest.TestCase):

    def setUp(self):
        self.json_formatter = savory_pie.formatters.JSONFormatter()

    def test_int(self):
        result = self.json_formatter.to_python_value(int, 15)
        self.assertEqual(15, result)

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
