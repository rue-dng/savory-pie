import json


class JSONFormatter(object):
    """
    Formatter reads and writes json while converting properties to and from
    javascript naming conventions and pep8.
    """

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
        return json.load(request)

    def write_to(self, body_dict, response):
        json.dump(body_dict, response)

    def to_python_value(self, type_, api_value):
        return None if api_value is None else type_(api_value)

    def to_api_value(self, type_, python_value):
        if type(python_value) not in (int, float, dict, list, bool, str, unicode, type(None)):
            return str(python_value)
        else:
            return python_value
