import functools
from savory_pie.resources import EmptyParams


def read_only_noop(func):
    @functools.wraps(func)
    def inner(self, *args, **kwargs):
        if not self._read_only:
            return func(self, *args, **kwargs)
    return inner


class Field(object):
    @property
    def name(self):
        name = getattr(self, '_attribute', getattr(self, '_full_attribute', None))
        if not name:
            raise Exception, u'Unable to determine name for field: {0}'.format(self)
        return name

    def schema(self, **kwargs):
        schema = kwargs.pop('schema', {})
        if getattr(self, '_type', None):
            return dict({'type': self._type.__name__}.items() + schema.items())
        return schema


class AttributeField(Field):
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

            ``read_only``
                optional -- this api will never try and set this value

        .. code-block:: python

            AttributeField('name', type=str)

        .. code-block:: javascript

            {'name': obj.name}

        .. code-block:: python

            AttributeField('other.age', type=int)

        .. code-block:: javascript

           {'age': obj.other.age}
    """
    def __init__(self,
                 attribute,
                 type,
                 published_property=None,
                 use_prefetch=False,
                 read_only=False):
        self._full_attribute = attribute
        self._type = type
        self._published_property = published_property
        self._read_only = read_only

    def _compute_property(self, ctx):
        if self._published_property is not None:
            return ctx.formatter.convert_to_public_property(self._published_property)
        else:
            return ctx.formatter.convert_to_public_property(self._bare_attribute)

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

    @read_only_noop
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


class URIResourceField(Field):
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

        ``read_only``
            optional -- this api will never try and set this value

        .. code-block:: python

            URIResourceField('other', OtherResource)

        .. code-block:: javascript

            {'other': '/api/other/{pk}'}
    """




    def __init__(self,
                 attribute,
                 resource_class,
                 published_property=None,
                 read_only=False):
        self._attribute = attribute
        self._resource_class = resource_class
        self._published_property = published_property
        self._read_only = read_only

    def _compute_property(self, ctx):
        if self._published_property is not None:
            return ctx.formatter.convert_to_public_property(self._published_property)
        else:
            return ctx.formatter.convert_to_public_property(self._attribute)

    @read_only_noop
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


class SubObjectResourceField(Field):
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

        ``read_only``
            optional -- this api will never try and set this value

        .. code-block:: python

            SubObjectResourceField('other', OtherResource)

        .. code-block:: javascript

            {'other': {'age': 9}}
    """
    def __init__(self,
                 attribute,
                 resource_class,
                 published_property=None,
                 read_only=False):
        self._attribute = attribute
        self._resource_class = resource_class
        self._published_property = published_property
        self._read_only = read_only

    def _compute_property(self, ctx):
        if self._published_property is not None:
            return ctx.formatter.convert_to_public_property(self._published_property)
        else:
            return ctx.formatter.convert_to_public_property(self._attribute)

    def get_subresource(self, ctx, source_dict, target_obj):
        """
        Extention point called by :meth:~`savory_pie.fields.handle_incoming` to
        build a resource class around the target attribute or return None if it
        is not found. Can try looking by resource_uri etc.
        """
        sub_source_dict = source_dict[self._compute_property(ctx)]
        resource = None
        if sub_source_dict is not None and 'resourceUri' in sub_source_dict:
            resource = ctx.resolve_resource_uri(sub_source_dict['resourceUri'])
        else:
            try:
                attribute = getattr(target_obj, self._attribute)
            except AttributeError:
                return None

            resource = self._resource_class(attribute)

        return resource

    def get_submodel(self, ctx, source_object):
        return getattr(source_object, self._attribute, None)

    @read_only_noop
    def handle_incoming(self, ctx, source_dict, target_obj):
        if not source_dict:
            setattr(target_obj, self._attribute, None)
        else:
            sub_resource = self.get_subresource(ctx, source_dict, target_obj)

            if not sub_resource: # creating a new resource
                sub_resource = self._resource_class.create_resource()

            sub_source_dict = source_dict[self._compute_property(ctx)]

            # this is to get around django-orm limitations, where in particular
            # if you have a one-to-one field, you can't set it to None since orm doesn't like it
            # so only set the attr to None, if what's coming in is None and what's there is not already None
            if sub_source_dict is None:
                if hasattr(target_obj, self._attribute) and getattr(target_obj, self._attribute) is not None:
                    setattr(target_obj, self._attribute, None)
            else:
                sub_resource.put(ctx, sub_source_dict)
                # Must be after the save on the sub_model
                setattr(target_obj, self._attribute, sub_resource.model)

    def handle_outgoing(self, ctx, source_obj, target_dict):
        sub_model = self.get_submodel(ctx, source_obj)
        if sub_model is None:
            target_dict[self._compute_property(ctx)] = None
        else:
            target_dict[self._compute_property(ctx)] =\
                self._resource_class(sub_model).get(ctx, EmptyParams())


class IterableField(Field):
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

        ``read_only``
            optional -- this api will never try and set this value

        .. code-block:: python

            RelatedManagerField('others', OtherResource)

        .. code-block:: javascript

            {'others': [{'age': 6}, {'age': 1}]}
    """
    def __init__(self,
                 attribute,
                 resource_class,
                 published_property=None,
                 read_only=False):
        self._attribute = attribute
        self._resource_class = resource_class
        self._published_property = published_property
        self._read_only = read_only

    def _compute_property(self, ctx):
        if self._published_property is not None:
            return ctx.formatter.convert_to_public_property(self._published_property)
        else:
            return ctx.formatter.convert_to_public_property(self._attribute)

    def _get_resource(self, ctx, manager, model_dict):
        resource = None
        if 'resourceUri' in model_dict:
            resource = ctx.resolve_resource_uri(model_dict['resourceUri'])
        elif '_id' in model_dict: # TODO what if you give an id that is not in the db?
            # TODO get key without the extra db lookup
            model = self._resource_class.get_from_queryset(manager.all(), model_dict['_id'])
            resource = self._resource_class(model)

        return resource

    def get_iterable(self, value):
        return value

    @read_only_noop
    def handle_incoming(self, ctx, source_dict, target_obj):
        manager = getattr(target_obj, self._attribute)

        db_keys = set()
        db_models = {}
        for model in manager.all():
            resource = self._resource_class(model)
            db_models[resource.key] = model
            db_keys.add(resource.key)

        new_models = []
        request_keys = set()
        request_models = {}
        for model_dict in source_dict[self._compute_property(ctx)]:
            resource = self._get_resource(ctx, manager, model_dict)
            if resource:
                request_models[resource.key] = resource.model
                request_keys.add(resource.key)
                if resource.key in db_keys:
                    resource.put(ctx, model_dict)
            else:
                model_resource = self._resource_class.create_resource()
                model_resource.put(ctx, model_dict)
                new_models.append(model_resource.model)

        manager.add(*new_models)

        models_to_remove = [db_models[key] for key in db_keys - request_keys]
        # If the FK is not nullable the manager will not have a remove
        if hasattr(manager, 'remove'):
            manager.remove(*models_to_remove)
        else:
            for model in models_to_remove:
                model.delete()

    def handle_outgoing(self, ctx, source_obj, target_dict):
        manager = getattr(source_obj, self._attribute)
        objects = []
        for model in manager.all():
            model_resource = self._resource_class(model)
            model_dict = model_resource.get(ctx, EmptyParams())
            # only add '_id' if there is no 'resourceUri'
            if 'resourceUri' not in model_dict:
                model_dict['_id'] = model_resource.key
            objects.append(model_dict)
        target_dict[self._compute_property(ctx)] = objects
