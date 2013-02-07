#protocol Field:
#    def handle_incoming(self, source_dict, target_obj)
#    def handle_outgoing(self, source_obj, target_dict)
#    def prepare(self, queryset)

class PropertyField(object):
    def __init__(self, property=None, json_property=None, type=None):
        self.property = property
        self.json_property = json_property or self.property
        self.type = type

    def handle_incoming(self, source_dict, target_obj):
        setattr(target_obj, self.property,
            self.serialize(source_dict[self.property])
        )

    def handle_outgoing(self, source_obj, target_dict):
        target_dict[self.property] = self.deserialize(
            getattr(source_obj, self.property)
        )

    def serialize(self, value):
        return value

    def deserialize(self, str):
        return self.type(str)

    def prepare(self, queryset):
        return queryset
