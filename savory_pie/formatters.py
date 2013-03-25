import json
import time
import pytz
from datetime import datetime, timedelta
import string
import re

class JSONFormatter(object):
    """
    Formatter reads and writes json while converting properties to and from
    javascript naming conventions and pep8.
    """

    content_type = 'application/json'

    dateRegex = re.compile('(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})\\.(\d+)([+-])(\d{2}):(\d{2})')

    def parse_datetime(self, s):

        m = self.dateRegex.match(str(s))
        if m is None:
            #This is what was done before, but it seems really weird
            #to silently return the input on error...
            return s

        year, month, date, hour, minute, second, milliseconds = \
            map(string.atoi, [m.group(i) for i in range(1, 8)])

        tz_op = m.group(8)

        tz_hour, tz_minute = \
            map(string.atoi, [m.group(i) for i in range(9, 11)])

        offset = tz_hour * 60 + tz_minute

        return datetime(year, month, date, hour, minute, second, milliseconds, pytz.FixedOffset(offset))

    def convert_to_public_property(self, bare_attribute):
        parts = bare_attribute.split('_')
        return ''.join([parts[0], ''.join(x.capitalize() for x in parts[1:])])

    def read_from(self, request):
        return json.load(request)

    def write_to(self, body_dict, response):
        json.dump(body_dict, response)

    # Not 100% happy with this API review pre 1.0
    def to_python_value(self, type_, api_value):
        if issubclass(type_, datetime):
            return self.parse_datetime(api_value)
        return None if api_value is None else type_(api_value)

    # Not 100% happy with this API review pre 1.0
    def to_api_value(self, type_, python_value):
        if issubclass(type_, datetime):
            if python_value:
                #Check if it is a naive date, and if so, make it UTC
                if not python_value.tzinfo:
                    python_value = python_value.replace(tzinfo=pytz.UTC)
                return python_value.isoformat("T") 
        elif type(python_value) not in (int, long, float, dict, list,
                                        bool, str, unicode, type(None)):
            return str(python_value)

        return python_value
