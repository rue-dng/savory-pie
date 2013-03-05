import json
import time
import datetime
import string
import re

class JSONFormatter(object):
    """
    Formatter reads and writes json while converting properties to and from
    javascript naming conventions and pep8.
    """

    class DateCapableEncoder(json.JSONEncoder):

        def default(self, obj):
            if isinstance(obj, datetime.datetime):
                return obj.strftime("%Y-%m-%dT%H:%M:%S")
            return json.JSONEncoder.default(self, obj)

    class DateCapableDecoder(json.JSONDecoder):

        dateRegex = re.compile('(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})')

        def decode(self, s):
            m = self.dateRegex.match(s)
            if m is not None:
                year, month, date, hour, minute, second = \
                    map(string.atoi, [m.group(i) for i in range(1, 7)])
                return datetime.datetime(year, month, date, hour, minute, second)
            return json.JSONDecoder.decode(self, s)

    content_type = 'application/json'

    def default_published_property(self, bare_attribute):
        js_name = []
        last_was_underscore = False

        for char in bare_attribute:
            if char == '_':
                last_was_underscore = True
            else:
                if last_was_underscore:
                    js_name.append(char.upper())
                else:
                    js_name.append(char)

                last_was_underscore = False

        return ''.join(js_name)

    def read_from(self, request):
        return json.load(request, cls=self.DateCapableDecoder)

    def write_to(self, body_dict, response):
        json.dump(body_dict, response, cls=self.DateCapableEncoder)

    def to_python_value(self, type_, api_value):
        if type_ is datetime.datetime:
            return json.loads(api_value, cls=self.DateCapableDecoder)
        return None if api_value is None else type_(api_value)

    def to_api_value(self, type_, python_value):
        if type(python_value) is datetime.datetime:
            return python_value.strftime("%Y-%m-%dT%H:%M:%S")
        elif type(python_value) not in (int, float, dict, list,
                                        bool, str, unicode, type(None)):
            return str(python_value)
        else:
            return python_value
