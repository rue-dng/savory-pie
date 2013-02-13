from savory_pie.utils import append_select_related

#protocol Field:

#    def handle_incoming(self, source_dict, target_obj)
#       Called by ModelResource.put or post to set Model properties on
#       target_obj based on information from the source_dict.

#    def handle_outgoing(self, source_obj, target_dict)
#       Called by ModelResource.get to set key on the target_dict based
#       on information in the Model source_obj.

#    def prepare(self, queryset)
#       Called by ModelResource.prepare to allow for select_related calls
#       on the queryset, so related collections objects can be retrieved
#       efficiently.

class PropertyField(object):
    """
    Simple Field that translates an object property to/from a dict.
    property - property on the Model
    type - expecting type of value - int, bool, etc.
    json_property - name under which the value is placed into the dict
        - by default - inferred from property
    """
    def __init__(self, property, type, json_property=None):
        self.property = property
        self.json_property = json_property or _python_to_js_name(self.property)
        self.type = type

    def handle_incoming(self, ctx, source_dict, target_obj):
        setattr(target_obj, self.property,
            self.serialize(source_dict[self.json_property])
        )

    def handle_outgoing(self, ctx, source_obj, target_dict):
        target_dict[self.json_property] = self.deserialize(
            getattr(source_obj, self.property)
        )

    def serialize(self, value):
        return value

    def deserialize(self, string):
        return None if string is None else self.type(string)

    def prepare(self, queryset):
        return queryset


class FKPropertyField(object):
    """
    Used to flatten fields of related models in to a single API object.

    FKPropertyField('other.name', type=int) will return this json {'name': other.name}
    """
    def __init__(self, property, type, json_property=None):
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

    def handle_incoming(self, ctx, source_dict, target_obj):
        self._set_property(
            target_obj,
            self.serialize(source_dict[self.json_property])
        )

    def handle_outgoing(self, ctx, source_obj, target_dict):
        target_dict[self.json_property] = self.deserialize(
            self._get_property(source_obj)
        )

    def serialize(self, value):
        return value

    def deserialize(self, str):
        return self.type(str)

    def prepare(self, queryset):
        segments = self.property.split('.')
        append_select_related(queryset, '__'.join(segments[:-1]))
        return queryset


class SubModelResourceField(object):
    def __init__(self, property, resource_class, json_property=None):
        self.property = property
        self.resource_class = resource_class
        self.json_property = json_property or _python_to_js_name(self.property)

    def handle_incoming(self, ctx, source_dict, target_obj):
        sub_model = getattr(target_obj, self.property, None)
        if sub_model is None:
            sub_resource = self.resource_class.create_resource()
            # I am not 100% happy with this
            setattr(target_obj, self.property, sub_resource.model)
        else:
            sub_resource = self.resource_class(sub_model)

        sub_resource.put(ctx, source_dict[self.json_property])

    def handle_outgoing(self, ctx, source_obj, target_dict):
        sub_model = getattr(source_obj, self.property)
        target_dict[self.json_property] = self.resource_class(sub_model).get(ctx)

    def prepare(self, queryset):
        append_select_related(queryset, self.property)
        return queryset


class RelatedManagerField(object):
    def __init__(self, property, resource_class, json_property=None):
        self.property = property
        self.resource_class = resource_class
        self.json_property = json_property or _python_to_js_name(self.property)

    def handle_incoming(self, ctx, source_dict, target_obj):
        # TODO something
        pass

    def handle_outgoing(self, ctx, source_obj, target_dict):
        manager = getattr(source_obj, self.property)
        # TODO assert manager/resource_class types are correct
        target_dict[self.json_property] = self.resource_class(manager.all()).get(ctx)['objects']

    def prepare(self, queryset):
        append_select_related(queryset, self.property)
        return queryset


def _python_to_js_name(python_name):
    js_name = []
    last_was_underscore = False

    for char in python_name:
        if char == '_':
            last_was_underscore = True
        else:
            if last_was_underscore:
                js_name.append(char.upper())
            else:
                js_name.append(char)

            last_was_underscore = False

    return ''.join(js_name)
