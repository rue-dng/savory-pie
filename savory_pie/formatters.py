import exceptions
import json
import pytz
import datetime
import re

from dateutil import parser


class JSONFormatter(object):
    """
    Formatter reads and writes json while converting properties to and from
    javascript naming conventions and pep8.
    """

    content_type = 'application/json'

    dateRegex = re.compile('(\d{4})-(\d{2})-(\d{2})(.*)')

    def parse_datetime(self, s):
        if s is None:
            return None
        if self.dateRegex.match(s):
            try:
                return parser.parse(s).astimezone(pytz.utc)
            except ValueError:
                return parser.parse(s).replace(tzinfo=pytz.utc)
        raise TypeError('Unable to parse ' + repr(s) + ' as a datetime')

    def parse_date(self, s):
        if s is None:
            return None
        if self.dateRegex.match(s):
            return parser.parse(s).date()
        raise TypeError('Unable to parse ' + repr(s) + ' as a datetime')

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
            if type_ is datetime.date:
                return self.parse_date(api_value)
            elif issubclass(type_, datetime.datetime):
                return self.parse_datetime(api_value)
            return None if api_value is None else type_(api_value)
        except (ValueError, exceptions.StandardError):
            raise TypeError('Expected ' + str(type_) + ', got ' + repr(api_value))

    # Not 100% happy with this API review pre 1.0
    def to_api_value(self, type_, python_value):
        if python_value is not None:
            if type_ is datetime.date:
                return python_value.strftime("%Y-%m-%d")
            elif issubclass(type_, datetime.datetime):
                #Check if it is a naive date, and if so, make it UTC
                if not python_value.tzinfo:
                    python_value = python_value.replace(tzinfo=pytz.UTC)
                return python_value.isoformat("T")
            elif type(python_value) not in (int, long, float, dict, list,
                                            bool, str, unicode, type(None)):
                return str(python_value)

        return python_value
