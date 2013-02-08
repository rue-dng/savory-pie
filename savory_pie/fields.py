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


class FKPropertyField(object):
    """
    Used to flatten fields of related models in to a single API object.

    FKPropertyField('other.name', type=int) will return this json {'name': other.name}
    """
    def __init__(self, property=None, json_property=None, type=None):
        self.property = property
        self.json_property = json_property or _python_to_js_name(self.property.split('.')[-1])
        self.type = type

    def _get_property(self, obj):
        property = obj
        for segment in self.property.split('.'):
            property = getattr(property, segment)
        return property

    def _set_property(self, obj, value):
        property = obj
        segments = self.property.split('.')
        for segment in segments[:-1]:
            property = getattr(property, segment)
        setattr(property, segments[-1], value)

    def handle_incoming(self, source_dict, target_obj):
        self._set_property(
            target_obj,
            self.serialize(source_dict[self.json_property])
        )

    def handle_outgoing(self, source_obj, target_dict):
        target_dict[self.json_property] = self.deserialize(
            self._get_property(source_obj)
        )

    def serialize(self, value):
        return value

    def deserialize(self, str):
        return self.type(str)

    def prepare(self, queryset):
        segments = self.property.split('.')
        queryset = queryset.select_related('__'.join(segments[:-1]))
        return queryset
