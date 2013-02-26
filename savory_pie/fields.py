from savory_pie.resources import EmptyParams

class AttributeField(object):
    """
    Simple Field that translates an object attribute to/from a dict.

        Parameters:

            ``attribute``
                attribute on the Model can be a multi-level expression - like
                related_entity.attribute

            ``type``
                expecting type of value -- int, bool, etc.

            ``published_property``
                optional -- name exposed in the API

        .. code-block:: python

            AttributeField('name', type=str)

        .. code-block:: javascript

            {'name': obj.name}

        .. code-block:: python

            AttributeField('other.age', type=int)

        .. code-block:: javascript

           {'age': obj.other.age}
    """
    def __init__(self, attribute, type, published_property=None, use_prefetch=False):
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


class URIResourceField(object):
    """
    Field that exposes just the URI of related entity


    Parameters:

        ``attribute``
            name of the relationship between the parent object and the related
            object may only be single level

        ``resource_class``
            a ModelResource -- used to represent the related object needs to be
            fully addressable

        ``published_property``
            optional -- name exposed in the API


        .. code-block:: python

            URIResourceField('other', OtherResource)

        .. code-block:: javascript

            {'other': '/api/other/{pk}'}
    """
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
        uri = source_dict[self._compute_property(ctx)]

        resource = ctx.resolve_resource_uri(uri)
        if resource is None:
            raise ValueError, 'invalid URI: ' + uri

        setattr(target_obj, self._attribute, resource.model)

    def handle_outgoing(self, ctx, source_obj, target_dict):
        sub_model = getattr(source_obj, self._attribute)
        resource = self._resource_class(sub_model)

        target_dict[self._compute_property(ctx)] = ctx.build_resource_uri(resource)


class SubObjectResourceField(object):
    """
    Field that embeds a single related resource into the parent object

    Parameters:

        ``attribute``
            name of the relationship between the parent object and the related
            object may only be single level

        ``resource_class``
            a ModelResource -- used to represent the related object

        ``published_property``
            optional -- name exposed in the API

        .. code-block:: python

            SubObjectResourceField('other', OtherResource)

        .. code-block:: javascript

            {'other': {'age': 9}}
    """
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

        sub_resource.put(ctx, source_dict[self._compute_property(ctx)])

    def handle_outgoing(self, ctx, source_obj, target_dict):
        sub_model = getattr(source_obj, self._attribute)
        target_dict[self._compute_property(ctx)] =\
            self._resource_class(sub_model).get(ctx, EmptyParams())


class IterableField(object):
    """
    Field that embeds a many relationship into the parent object

    Parameters:

        ``attribute``
            name of the relationship between the parent object and the related
            objects may only be single level

        ``resource_class``
            a ModelResource -- used to represent the related objects

        ``published_property``
            optional name exposed through the API

        .. code-block:: python

            RelatedManagerField('others', OtherResource)

        .. code-block:: javascript

            {'others': [{'age': 6}, {'age': 1}]}
    """
    def __init__(self, attribute, resource_class, published_property=None):
        self._attribute = attribute
        self._resource_class = resource_class
        self._published_property = published_property

    def _compute_property(self, ctx):
        if self._published_property is not None:
            return self._published_property
        else:
            return ctx.formatter.default_published_property(self._attribute)

    def get_iterable(self, value):
        return value

    def handle_incoming(self, ctx, source_dict, target_obj):
        # TODO something
        pass

    def handle_outgoing(self, ctx, source_obj, target_dict):
        manager = getattr(source_obj, self._attribute)
        objects = []
        for model in manager.all():
            objects.append(self._resource_class(model).get(ctx, EmptyParams()))
        target_dict[self._compute_property(ctx)] = objects
