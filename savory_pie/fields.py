#protocol Field:
#    def handle_incoming(self, source_dict, target_obj)
#    def handle_outgoing(self, source_obj, target_dict)
#    def prepare(self, queryset)

def _python_to_js_name(python_name):
    # TODO: Give me a real implementation
    return python_name

class PropertyField(object):
    def __init__(self, property, type, json_property=None):
        self.property = property
        self.json_property = json_property or _python_to_js_name(self.property)
        self.type = type

    def handle_incoming(self, source_dict, target_obj):
        setattr(target_obj, self.property,
            self.serialize(source_dict[self.json_property])
        )

    def handle_outgoing(self, source_obj, target_dict):
        target_dict[self.json_property] = self.deserialize(
            getattr(source_obj, self.property)
        )

    def serialize(self, value):
        return value

    def deserialize(self, str):
        return self.type(str)

    def prepare(self, queryset):
        return queryset