import json

#protocol Formatter
#   def default_published_name(self, attribute)
#   def to_python_value(type_, api_value)
#   def to_api_value(type_, python_value)


class JSONFormatter(object):
    content_type = 'application/json'

    def default_published_name(self, python_attribute):
        js_name = []
        last_was_underscore = False

        for char in python_attribute:
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
        return python_value