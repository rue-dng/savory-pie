import unittest
import decimal

import savory_pie.formatters


class JSONToAPITest(unittest.TestCase):

    def setUp(self):
        self.json_formater = savory_pie.formatters.JSONFormatter()

    def test_int(self):
        result = self.json_formater.to_api_value(int, 15)
        self.assertEqual(15, result)

    def test_float(self):
        result = self.json_formater.to_api_value(float, 15.5)
        self.assertEqual(15.5, result)

    def test_dict(self):
        result = self.json_formater.to_api_value(dict, {'a': 1, 'b': 2})
        self.assertEqual({'a': 1, 'b': 2}, result)

    def test_list(self):
        result = self.json_formater.to_api_value(list, [1, 2, 3])
        self.assertEqual([1, 2, 3], result)

    def test_bool(self):
        result = self.json_formater.to_api_value(bool, True)
        self.assertEqual(True, result)

    def test_str(self):
        result = self.json_formater.to_api_value(str, 'abc')
        self.assertEqual('abc', result)

    def test_unicode(self):
        result = self.json_formater.to_api_value(unicode, u'abc\U0001F4A9')
        self.assertEqual(u'abc\U0001F4A9', result)

    def test_none(self):
        result = self.json_formater.to_api_value(unicode, None)
        self.assertEqual(None, result)

    def test_decimal(self):
        result = self.json_formater.to_api_value(decimal.Decimal, decimal.Decimal('5.10'))
        self.assertEqual('5.10', result)


class JSONToPython(unittest.TestCase):

    def setUp(self):
        self.json_formater = savory_pie.formatters.JSONFormatter()

    def test_int(self):
        result = self.json_formater.to_python_value(int, 15)
        self.assertEqual(15, result)

    def test_float(self):
        result = self.json_formater.to_python_value(float, 15.5)
        self.assertEqual(15.5, result)

    def test_dict(self):
        result = self.json_formater.to_python_value(dict, {'a': 1, 'b': 2})
        self.assertEqual({'a': 1, 'b': 2}, result)

    def test_list(self):
        result = self.json_formater.to_python_value(list, [1, 2, 3])
        self.assertEqual([1, 2, 3], result)

    def test_bool(self):
        result = self.json_formater.to_python_value(bool, True)
        self.assertEqual(True, result)

    def test_str(self):
        result = self.json_formater.to_python_value(str, 'abc')
        self.assertEqual('abc', result)

    def test_unicode(self):
        result = self.json_formater.to_python_value(unicode, u'abc\U0001F4A9')
        self.assertEqual(u'abc\U0001F4A9', result)

    def test_none(self):
        result = self.json_formater.to_python_value(unicode, None)
        self.assertEqual(None, result)

    def test_decimal(self):
        result = self.json_formater.to_python_value(decimal.Decimal, '5.10')
        self.assertEqual(decimal.Decimal('5.10'), result)
