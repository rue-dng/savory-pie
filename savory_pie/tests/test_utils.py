import mock
import unittest
from savory_pie import utils
from savory_pie.utils import ParamsDict


class ToListTest(unittest.TestCase):

    def test_to_list_splits_on_comma(self):
        ids_param = '1,2,3,4,5'
        self.assertEqual(utils.to_list(ids_param), ['1', '2', '3', '4', '5'])

    def test_to_list_bad_data(self):
        march_15_timestamp = 12345
        self.assertEqual(utils.to_list(march_15_timestamp), 12345)

    def test_not_list_split(self):
        item = mock.Mock()
        item.split.return_value = 'Something'
        self.assertEqual(utils.to_datetime(item), item)


class ToDateTimeTest(unittest.TestCase):

    def test_to_datetime(self):
        march_15_timestamp = 1363320000000
        march_15_datetime = utils.to_datetime(march_15_timestamp)

        self.assertEqual(march_15_datetime.year, 2013)
        self.assertEqual(march_15_datetime.month, 3)
        self.assertEqual(march_15_datetime.day, 15)

    def test_to_datetime_bad_date(self):
        march_15_timestamp = 'something'
        self.assertEqual(utils.to_datetime(march_15_timestamp), 'something')


class ParamsDictTestCase(unittest.TestCase):

    def test_parameters_contains(self):
        params = ParamsDict({'key1': 'value1'})
        self.assertTrue('key1' in params)

    def test_parameters_get(self):
        params = ParamsDict({'key1': 'value1'})
        self.assertEqual(params.get('key1', 'other'), 'value1')

    def test_parameters_get_default(self):
        params = ParamsDict({'key1': 'value1'})
        self.assertEqual(params.get('some', 'other'), 'other')

    def test_parameters_get_as(self):
        params = ParamsDict({'key1': 'value1'})
        self.assertEqual(params.get_as('key1', str, 'other'), 'value1')

    def test_parameters_get_as_wrong_type(self):
        params = ParamsDict({'key1': 1})
        self.assertEqual(params.get_as('key1', str, 'other'), '1')

    def test_parameters_get_as_default(self):
        params = ParamsDict({'key1': 1})
        self.assertEqual(params.get_as('key2', str, 'other'), 'other')

    def test_parameters_get_list(self):
        params = ParamsDict({'key1': 'value1'})
        self.assertEqual(params.get_list('key1'), ['value1'])

    def test_get_error(self):
        params = ParamsDict({'key1': 'value1'})
        with self.assertRaises(KeyError):
            params['key2']

    def test_get_error2(self):
        params = ParamsDict({'key1': 'value1'})
        self.assertEqual(params['key1'], 'value1')

    def test_keys(self):
        params = ParamsDict({'key1': 'value1'})
        self.assertEqual(params.keys(), ['key1'])

    def test_get_list_of(self):
        params = ParamsDict({'key1': [1]})
        self.assertEqual(params.get_list_of('key1', str), ['1'])

    def test_get_list_of_not_found(self):
        params = ParamsDict({'key1': [1]})
        self.assertEqual(params.get_list_of('key2', str), [])
