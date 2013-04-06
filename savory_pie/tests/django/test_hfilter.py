import datetime
import os
import unittest
import pytz

from mock import Mock

from django.http import QueryDict
from django.core.management import call_command

from savory_pie.tests.mock_context import mock_context
from savory_pie.formatters import JSONFormatter
from savory_pie.tests.django.hfilter.models import User, UserResource, UserQuerySetResource

os.environ['DJANGO_SETTINGS_MODULE']='savory_pie.tests.django.dummy_settings'


class TestParams(object):

    def __init__(self, filters):
        # we need our query string to be camel cased, since in StandardFilter, we convert these strings
        # Note, since we are calling default_publish_property on the filter names,
        # Camel casing should be applied to filter names, but NOT to parameters.
        formatted_names = []
        for name, value in filters.items():
            formatted_names.append(JSONFormatter().convert_to_public_property(name)
                                   + '=' + str(value))
        self.querystring = "&".join(formatted_names).replace("+", "%2B")
        self._GET = QueryDict(self.querystring)

now = datetime.datetime.now(tz=pytz.UTC).replace(microsecond=0)
hour = datetime.timedelta(hours=1)

# helpful debug stuff: https://gist.github.com/wware/5336328


class HaystackFilterTest(unittest.TestCase):

    def setUp(self):
        call_command('syncdb', verbosity=0)
        User(name='alice', age=31, when=now-hour).save()
        User(name='bob', age=20, when=now-hour).save()
        User(name='charlie', age=26, when=now-hour).save()
        call_command('rebuild_index', interactive=False, verbosity=0)

    def tearDown(self):
        User.objects.all().delete()

    def apply_filters(self, filters):
        ctx = mock_context()
        queryset = User.objects.get_query_set()
        params = TestParams(filters)

        for filter in UserQuerySetResource.filters:
            queryset = filter.filter(ctx, params, queryset)
        return queryset

    def test_names(self):
        for name in ('alice', 'bob', 'charlie'):
            results = self.apply_filters({'haystack': name})
            self.assertEqual(1, results.count())
            self.assertEqual([name], [x.name for x in results])

    def test_ages(self):
        for age, name in ((31, 'alice'), (20, 'bob'), (26, 'charlie')):
            results = self.apply_filters({'haystack': age})
            self.assertEqual(1, results.count())
            self.assertEqual([name], [x.name for x in results])
