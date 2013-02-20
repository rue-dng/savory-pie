from savory_pie.utils import append_select_related

#protocol Field:
#    def handle_incoming(self, source_dict, target_obj)
#       Called by ModelResource.put or post to set Model properties on
#       target_obj based on information from the source_dict.

#    def handle_outgoing(self, ctx, source_obj, target_dict)
#       Called by ModelResource.get to set key on the target_dict based
#       on information in the Model source_obj.

#    def prepare(self, ctx, queryset)
#       Called by ModelResource.prepare to allow for select_related calls
#       on the queryset, so related collections objects can be retrieved
#       efficiently.

class AttributeField(object):
    """
    Simple Field that translates an object property to/from a dict.
    attribute - attribute on the Model
        - can be a multi-level expression - like related_entity.attribute
    type - expecting type of value - int, bool, etc.
    published_property - name under which the value is placed into the dict
    - by default - inferred from property

    Used to flatten fields of related models in to a single API object.

    AttributeField('other.name', type=int) will return this json {'name': other.name}
    """
    def __init__(self, attribute, type, published_property=None):
        self._full_attribute = attribute
        self._type = type
        self._published_property = published_property

    def _compute_property(self, ctx):
        if self._published_property is not None:
            return self._published_property
        else:
            return ctx.formatter.default_published_property(self._bare_attribute)

    @property
    def _bare_attribute(self):
        return self._full_attribute.split('.')[-1]

    @property
    def _attrs(self):
        return self._full_attribute.split('.')

    def _get_object(self, root_obj):
        obj = root_obj
        for attr in self._attrs[:-1]:
            obj = getattr(obj, attr)
            if obj is None:
                return None
        return obj

    def _get(self, obj):
        obj = self._get_object(obj)
        if obj is None:
            return None
        else:
            return getattr(obj, self._bare_attribute)

    def _set(self, obj, value):
        obj = self._get_object(obj)
        # TODO: handle None
        return setattr(obj, self._bare_attribute, value)

    def handle_incoming(self, ctx, source_dict, target_obj):
        self._set(
            target_obj,
            self.to_python_value(ctx, source_dict[self._compute_property(ctx)])
        )

    def handle_outgoing(self, ctx, source_obj, target_dict):
        target_dict[self._compute_property(ctx)] = self.to_api_value(
            ctx,
            self._get(source_obj)
        )

    def to_python_value(self, ctx, api_value):
        return ctx.formatter.to_python_value(self._type, api_value)

    def to_api_value(self, ctx, python_value):
        return ctx.formatter.to_api_value(self._type, python_value)

    def prepare(self, ctx, related):
        related.select('__'.join(self._attrs[:-1]))


class SubModelResourceField(object):
    def __init__(self, attribute, resource_class, published_property=None):
        self._attribute = attribute
        self._resource_class = resource_class
        self._published_property = published_property

    def _compute_property(self, ctx):
        if self._published_property is not None:
            return self._published_property
        else:
            return ctx.formatter.default_published_property(self._attribute)

    def handle_incoming(self, ctx, source_dict, target_obj):
        sub_model = getattr(target_obj, self._attribute, None)
        if sub_model is None:
            sub_resource = self._resource_class.create_resource()
            # I am not 100% happy with this
            setattr(target_obj, self._attribute, sub_resource.model)
        else:
            sub_resource = self._resource_class(sub_model)

        sub_resource.put(ctx, source_dict[self._attribute])

    def handle_outgoing(self, ctx, source_obj, target_dict):
        sub_model = getattr(source_obj, self._attribute)
        target_dict[self._compute_property(ctx)] = self._resource_class(sub_model).get(ctx)

    def prepare(self, ctx, related):
        related.select(self._attribute)


class RelatedManagerField(object):
    def __init__(self, attribute, resource_class, published_property=None):
        self._attribute = attribute
        self._resource_class = resource_class
        self._published_property = published_property

    def _compute_property(self, ctx):
        if self._published_property is not None:
            return self._published_property
        else:
            return ctx.formatter.default_published_property(self._attribute)

    def handle_incoming(self, ctx, source_dict, target_obj):
        # TODO something
        pass

    def handle_outgoing(self, ctx, source_obj, target_dict):
        manager = getattr(source_obj, self._attribute)
        # TODO assert manager/resource_class types are correct
        target_dict[self._compute_property(ctx)] = \
            self._resource_class(manager.all()).get(ctx)['objects']

    def prepare(self, ctx, related):
        related.prefetch(self._attribute)
