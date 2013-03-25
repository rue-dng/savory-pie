import json
import time
from datetime import datetime, timedelta
import string
import re

class FormatException(Exception):
    pass

class JSONFormatter(object):
    """
    Formatter reads and writes json while converting properties to and from
    javascript naming conventions and pep8.
    """

    content_type = 'application/json'

    dateRegex = re.compile('(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})\\.(\d+)([+-])(\d{2}):(\d{2})')

    def parse_datetime(self, s):

        print s

        m = self.dateRegex.match(s)
        if m is None:
            raise FormatException("Invalid date format")

        for i in range(1, 10):
            print str(i) + ":" + m.group(i)
            
        year, month, date, hour, minute, second, milliseconds = \
            map(string.atoi, [m.group(i) for i in range(1, 8)])

        tz_op = m.group(7)

        tz_hour, tz_minute = \
            map(string.atoi, [m.group(i) for i in range(8, 10)])

        offset = timedelta(hours=tz_hour, minute=tz_minute)
        date = datetime(year, month, date, hour, minute, second, milliseconds)
        if tz_op == "-":
            return date - offset
        elif tz_op == "+":
            return date + offset

    def default_published_property(self, bare_attribute):
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
            return python_value.isoformat("T") 
        elif type(python_value) not in (int, long, float, dict, list,
                                        bool, str, unicode, type(None)):
            return str(python_value)
        else:
            return python_value
