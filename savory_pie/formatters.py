import json
import time
import pytz
import string
import datetime
import re

class JSONFormatter(object):
    """
    Formatter reads and writes json while converting properties to and from
    javascript naming conventions and pep8.
    """

    content_type = 'application/json'

    dateTimeRegex = re.compile('(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})\\.(\d+)([+-])(\d{2}):(\d{2})')
    dateRegex = re.compile('(\d{4})-(\d{2})-(\d{2})(.*)')

    def parse_datetime(self, s):

        m = self.dateTimeRegex.match(str(s))
        if m is None:
            raise TypeError('Unable to parse ' + repr(s) + ' as a datetime')

        year, month, date, hour, minute, second, milliseconds = \
            map(string.atoi, [m.group(i) for i in range(1, 8)])

        tz_op = m.group(8)

        tz_hour, tz_minute = \
            map(string.atoi, [m.group(i) for i in range(9, 11)])

        offset = tz_hour * 60 + tz_minute

        return datetime.datetime(year, month, date, hour, minute, second, milliseconds, pytz.FixedOffset(offset))

    def parse_date(self, s):
        if s is None:
            return None
        m = self.dateRegex.match(s)
        if m is None:
            raise TypeError('Unable to parse ' + repr(s) + ' as a date')
        year, month, date = map(int, [m.group(i) for i in range(1, 4)])
        return datetime.date(year, month, date)

    def convert_to_public_property(self, bare_attribute):
        parts = bare_attribute.split('_')
        return ''.join([parts[0], ''.join(x.capitalize() for x in parts[1:])])

    def read_from(self, request):
        return json.load(request)

    def write_to(self, body_dict, response):
        json.dump(body_dict, response)

    # Not 100% happy with this API review pre 1.0
    def to_python_value(self, type_, api_value):
        try:
            if issubclass(type_, datetime.datetime):
                return self.parse_datetime(api_value)
            elif issubclass(type_, datetime.date):
                return self.parse_date(api_value)
            return None if api_value is None else type_(api_value)
        except ValueError:
            raise TypeError('Expected ' + str(type_) + ', got ' + repr(api_value))

    # Not 100% happy with this API review pre 1.0
    def to_api_value(self, type_, python_value):
        if python_value is not None:
            if issubclass(type_, datetime.datetime):
            	if python_value:
                	#Check if it is a naive date, and if so, make it UTC
                    if not python_value.tzinfo:
                    	python_value = python_value.replace(tzinfo=pytz.UTC)
                    return python_value.isoformat("T") 
            elif issubclass(type_, datetime.date):
            	return python_value.strftime("%Y-%m-%d")
            elif type(python_value) not in (int, long, float, dict, list,
                                            bool, str, unicode, type(None)):
                return str(python_value)

        return python_value
