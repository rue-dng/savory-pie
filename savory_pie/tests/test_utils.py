import unittest
from savory_pie import utils


class ToListTest(unittest.TestCase):

    def test_to_list_splits_on_comma(self):
        ids_param = '1,2,3,4,5'
        self.assertEqual(utils.to_list(ids_param), ['1', '2', '3', '4', '5'])


class ToDateTimeTest(unittest.TestCase):

    def test_to_datetime(self):
        march_15_timestamp = 1363320000000
        march_15_datetime = utils.to_datetime(march_15_timestamp)

        self.assertEqual(march_15_datetime.year, 2013)
        self.assertEqual(march_15_datetime.month, 3)
        self.assertEqual(march_15_datetime.day, 15)
