import collections
import functools
import importlib
from savory_pie.auth import authorization, authorization_adapter
from savory_pie.resources import EmptyParams
from savory_pie.django.validators import validate, ValidationError
from savory_pie.errors import SavoryPieError


def read_only_noop(func):
    @functools.wraps(func)
    def inner(self, *args, **kwargs):
        if not self._read_only:
            return func(self, *args, **kwargs)
    return inner


class ResourceClassUser(type):
    def __new__(cls, name, bases, d):

        def init_resource_class(self, rclass):
            self._arg_resource_class = rclass
            if isinstance(rclass, str) or isinstance(rclass, unicode):
                self._real_resource_class = None
            else:
                self._real_resource_class = rclass

        def getter(self):
            if self._real_resource_class is None and \
                    self._arg_resource_class is not None:
                rclass = self._arg_resource_class
                n = rclass.rindex('.')
                module = importlib.import_module(rclass[:n])
                self._real_resource_class = getattr(module, rclass[n + 1:])
            return self._real_resource_class

        def setter(self, value):
            self._real_resource_class = value

        deler = None
        d['init_resource_class'] = init_resource_class
        d['_resource_class'] = property(getter, setter, deler, '')
        return type.__new__(cls, name, bases, d)


class Field(object):
    @property
    def name(self):
        name = getattr(self, '_attribute', None) or getattr(self, '_full_attribute', None)
        if not name:
            raise SavoryPieError(u'Unable to determine name for field: {0}'.format(self))
        return name

    def schema(self, ctx, **kwargs):
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

            ``optional``
                optional -- if missing, will not throw a ValidationError

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
                 read_only=False,
                 validator=None,
                 optional=False,
                 permission=None):
        self._full_attribute = attribute
        self._type = type
        self._published_property = published_property
        self._read_only = read_only
        self._optional = optional
        self.validator = validator or []
        self.permission = permission

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
    @authorization(authorization_adapter)
    def handle_incoming(self, ctx, source_dict, target_obj):
        attr = self._compute_property(ctx)
        if attr not in source_dict:
            if self._optional:
                return
            raise ValidationError(self, {'missingField': attr,
                                         'target': type(target_obj).__name__})
        with ctx.target(target_obj):
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

    def validate_resource(self, ctx, key, resource, value):
        error_dict = {}
        if isinstance(self.validator, collections.Iterable):
            for validator in self.validator:
                validator.find_errors(error_dict, ctx, key, resource, self, value)
        else:
            self.validator.find_errors(error_dict, ctx, key, resource, self, value)
        return error_dict


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
    __metaclass__ = ResourceClassUser

    def __init__(self,
                 attribute,
                 resource_class,
                 published_property=None,
                 read_only=False,
                 validator=None,
                 permission=None):
        self._attribute = attribute
        self.init_resource_class(resource_class)
        self._published_property = published_property
        self._read_only = read_only
        self.validator = validator or []
        self.permission = permission

    def _compute_property(self, ctx):
        if self._published_property is not None:
            return ctx.formatter.convert_to_public_property(self._published_property)
        else:
            return ctx.formatter.convert_to_public_property(self._attribute)

    @read_only_noop
    @authorization(authorization_adapter)
    def handle_incoming(self, ctx, source_dict, target_obj):
        uri = source_dict[self._compute_property(ctx)]
        if uri is not None:
            resource = ctx.resolve_resource_uri(uri)
            if resource is None:
                raise ValueError('invalid URI {0}: '.format(uri))

            setattr(target_obj, self._attribute, resource.model)
        else:
            setattr(target_obj, self._attribute, None)

    def handle_outgoing(self, ctx, source_obj, target_dict):
        sub_model = getattr(source_obj, self._attribute)
        if sub_model is not None:
            resource = self._resource_class(sub_model)
            target_dict[self._compute_property(ctx)] = ctx.build_resource_uri(resource)
        else:
            target_dict[self._compute_property(ctx)] = None

    def validate_resource(self, ctx, key, resource, source_dict):
        error_dict = {}
        # TODO how do we validate this guy?
        return error_dict


class CompleteURIResourceField(Field):
    """
    Field that exposes just the URI of the complete entity of itself.
    This is useful if a resource is explicitly not including resource_uris, due to recursive inclusion,
    this field can be used, to link to the URI of the full resource version of itself.
    It adds a hard coded 'completeResourceUri' entry to the target dictionary.

    Parameters:

        ``resource_class``
            a ModelResource -- used to represent the related object needs to be
            fully addressable

        .. code-block:: python

            CompleteURIResourceField(OtherResource)

        .. code-block:: javascript

            {'completeResourceUri': '/api/other/{pk}'}
    """
    __metaclass__ = ResourceClassUser

    def __init__(self, resource_class, read_only=False, permission=None):
        self.init_resource_class(resource_class)
        self._read_only = read_only
        self.permission = permission

    @authorization(authorization_adapter)
    def handle_incoming(self, ctx, source_dict, target_obj):
        pass

    def handle_outgoing(self, ctx, source_obj, target_dict):
        resource = self._resource_class(source_obj)
        property_name = ctx.formatter.convert_to_public_property('complete_resource_uri')
        target_dict[property_name] = ctx.build_resource_uri(resource)


class URIListResourceField(Field):
    """
    Field that exposes a list of URIs of related entity, this allows for a many to many relationship.


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

            URIListResourceField('others', OtherResource)

        .. code-block:: javascript

            {'others': ['/api/other/{pk_1}', '/api/other/{pk_2}']
    """
    __metaclass__ = ResourceClassUser

    def __init__(self,
                 attribute,
                 resource_class,
                 published_property=None,
                 read_only=False,
                 validator=None,
                 permission=None):
        self._attribute = attribute
        self.init_resource_class(resource_class)
        self._published_property = published_property
        self._read_only = read_only
        self.validator = validator or []
        self.permission = permission

    def _compute_property(self, ctx):
        if self._published_property is not None:
            return ctx.formatter.convert_to_public_property(self._published_property)
        else:
            return ctx.formatter.convert_to_public_property(self._attribute)

    def get_iterable(self, value):
        return value

    @read_only_noop
    @authorization(authorization_adapter)
    def handle_incoming(self, ctx, source_dict, target_obj):
        attribute = getattr(target_obj, self._attribute)

        db_keys = set()
        db_models = {}
        for model in self.get_iterable(attribute):
            resource = self._resource_class(model)
            db_models[resource.key] = model
            db_keys.add(resource.key)

        new_models = []
        request_keys = set()

        for resource_uri in source_dict[self._compute_property(ctx)]:
            resource = ctx.resolve_resource_uri(resource_uri)
            if resource:
                request_keys.add(resource.key)

                if resource.key not in db_keys:
                    new_models.append(resource.model)
            else:
                raise SavoryPieError(u'Unable to resolve resource uri {0}'.format(resource_uri))

        # Delete before add to prevent problems with unique constraints
        models_to_remove = [db_models[key] for key in db_keys - request_keys]
        # If the FK is not nullable the attribute will not have a remove
        if hasattr(attribute, 'remove'):
            attribute.remove(*models_to_remove)
        else:
            for model in models_to_remove:
                model.delete()

        if hasattr(attribute, 'add'):
            attribute.add(*new_models)
        else:
            for obj in new_models:
                through_parameters = {
                    attribute.source_field_name: target_obj,
                    attribute.target_field_name: obj
                }
                attribute.through.objects.create(**through_parameters)

    def handle_outgoing(self, ctx, source_obj, target_dict):
        attrs = self._attribute.split('.')
        attribute = source_obj

        for attr in attrs:
            attribute = getattr(attribute, attr)
            if attribute is None:
                return None

        resource_uris = []
        for model in self.get_iterable(attribute):
            model_resource = self._resource_class(model)
            resource_uris.append(ctx.build_resource_uri(model_resource))
        target_dict[self._compute_property(ctx)] = resource_uris


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

        ``validator``
            optional -- a ResourceValidator, or list/tuple of ResourceValidators, to
            validate the data in the related object

        .. code-block:: python

            SubObjectResourceField('other', OtherResource)

        .. code-block:: javascript

            {'other': {'age': 9}}
    """
    __metaclass__ = ResourceClassUser

    def __init__(self,
                 attribute,
                 resource_class,
                 published_property=None,
                 read_only=False,
                 validator=None,
                 permission=None):
        self._attribute = attribute
        self.init_resource_class(resource_class)
        self._published_property = published_property
        self._read_only = read_only
        self.validator = validator or []
        self.permission = permission

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
        # TODO: clean up later per bug JRUT-4708
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

    def pre_save(self, model):
        return True

    @read_only_noop
    @authorization(authorization_adapter)
    def handle_incoming(self, ctx, source_dict, target_obj):
        if not source_dict:
            setattr(target_obj, self._attribute, None)
        else:
            sub_resource = self.get_subresource(ctx, source_dict, target_obj)

            if not sub_resource:  # creating a new resource
                sub_resource = self._resource_class.create_resource()

            sub_source_dict = source_dict[self._compute_property(ctx)]

            # this is to get around django-orm limitations, where in particular
            # if you have a one-to-one field, you can't set it to None since orm doesn't like it
            # so only set the attr to None, if what's coming in is None and what's there is not already None
            if sub_source_dict is None:
                if hasattr(target_obj, self._attribute) \
                   and getattr(target_obj, self._attribute) is not None \
                   and getattr(target_obj, self._attribute).pk:
                    setattr(target_obj, self._attribute, None)
            else:
                # Use the pre_save property, to determine whether we need to set the attribute before or after put
                # in the case of a ReverseSingleRelatedObject (pre_save is False), then we need to set the attribute first
                # before calling put. This is to get around the Django ORM restrictions.
                if not self.pre_save(target_obj):
                    setattr(target_obj, self._attribute, sub_resource.model)

                with ctx.target(target_obj):
                    sub_resource.put(
                        ctx,
                        sub_source_dict,
                        skip_validation=getattr(self, '_skip_validation', False)
                    )

                if self.pre_save(target_obj):
                    setattr(target_obj, self._attribute, sub_resource.model)

    def handle_outgoing(self, ctx, source_obj, target_dict):
        sub_model = self.get_submodel(ctx, source_obj)
        if sub_model is None:
            target_dict[self._compute_property(ctx)] = None
        else:
            target_dict[self._compute_property(ctx)] =\
                self._resource_class(sub_model).get(ctx, EmptyParams())

    def validate_resource(self, ctx, key, resource, source_dict):
        return validate(ctx, key + '.' + self.name, self._resource_class, source_dict)


class IterableField(Field):
    """
    Field that embeds a many relationship into the parent object

    Parameters:

        ``attribute``
            name of the relationship between the parent object and the related
            objects can be a multi-level expression - like related_entity.many_to_many_field

        ``resource_class``
            a ModelResource -- used to represent the related objects

        ``published_property``
            optional name exposed through the API

        ``read_only``
            optional -- this api will never try and set this value

        ``iterable_factory``
            optional -- a callable which is passed the attribute and returns an
            iterable this fields exports

        .. code-block:: python

            RelatedManagerField('others', OtherResource)

        .. code-block:: javascript

            {'others': [{'age': 6}, {'age': 1}]}
    """
    __metaclass__ = ResourceClassUser

    def __init__(self,
                 attribute,
                 resource_class,
                 published_property=None,
                 read_only=False,
                 iterable_factory=None,
                 validator=None,
                 permission=None):
        self._attribute = attribute
        self.init_resource_class(resource_class)
        self._published_property = published_property
        self._read_only = read_only
        self._iterable_factory = iterable_factory
        self.validator = validator or []
        self.permission = permission

    def _compute_property(self, ctx):
        if self._published_property is not None:
            return ctx.formatter.convert_to_public_property(self._published_property)
        else:
            return ctx.formatter.convert_to_public_property(self._attribute)

    def _get_resource(self, ctx, attribute, model_dict):
        resource = None
        if 'resourceUri' in model_dict:
            resource = ctx.resolve_resource_uri(model_dict['resourceUri'])
        elif '_id' in model_dict:  # TODO what if you give an id that is not in the db?
            # TODO get key without the extra db lookup
            model = self._resource_class.get_from_queryset(
                attribute.all(),
                model_dict['_id']
            )
            resource = self._resource_class(model)
        return resource

    def get_iterable(self, value):
        return value

    @property
    def _bare_attribute(self):
        return self._attribute.split('.')[-1]

    @read_only_noop
    @authorization(authorization_adapter)
    def handle_incoming(self, ctx, source_dict, target_obj):
        attribute = getattr(target_obj, self._attribute)

        # We are doing this outside of get_iterable so that subclasses can not
        # remove this override.
        if self._iterable_factory:
            iterable = self._iterable_factory(attribute)
        else:
            iterable = self.get_iterable(attribute)

        db_keys = set()
        db_models = {}
        for model in iterable:
            resource = self._resource_class(model)
            db_models[resource.key] = model
            db_keys.add(resource.key)

        new_models = []
        new_put_data = []
        request_keys = set()
        request_models = {}
        for model_dict in source_dict.get(self._compute_property(ctx), []):
            resource = self._get_resource(ctx, attribute, model_dict)
            if resource:
                request_models[resource.key] = resource.model
                request_keys.add(resource.key)
                # Check to see if the resource has already been saved in the DB
                if resource.key in db_keys:
                    with ctx.target(resource.model):
                        resource.put(ctx, model_dict)
                    # If the resource has been saved to the db and the model is
                    # a RelatedManager that is a through (existence of add attribute)
                    # must add it to the new model since it can create a model based
                    # on just the association.
                    if not hasattr(attribute, 'add'):
                        new_models.append(resource.model)
                else:
                    # if the model is not in the database, must save it
                    new_models.append(resource.model)

            else:
                # if the resource does not exist then this is a new instance
                new_put_data.append(model_dict)

        # Delete before add to prevent problems with unique constraints
        models_to_remove = [db_models[key] for key in db_keys - request_keys]
        # If the FK is not nullable the attribute will not have a remove
        if hasattr(attribute, 'remove'):
            attribute.remove(*models_to_remove)
        else:
            for obj in models_to_remove:
                # ManyRelatedManager
                if hasattr(attribute, 'through'):
                    through_params = {
                        attribute.source_field_name: target_obj,
                        attribute.target_field_name: obj
                    }
                    # only delete intermediary model instance if it already exists
                    for instance in attribute.through.objects.filter(**through_params):
                        instance.delete()
                # RelatedManager
                else:
                    obj.delete()

        # Delay all the new creates untill after the deletes for unique
        # constraints again
        for model_dict in new_put_data:
            model_resource = self._resource_class.create_resource()
            with ctx.target(target_obj):
                model_resource.put(ctx, model_dict, save=True)
            new_models.append(model_resource.model)

        if hasattr(attribute, 'add'):
            attribute.add(*new_models)
        else:
            for obj in new_models:
                through_params = {
                    attribute.source_field_name: target_obj,
                    attribute.target_field_name: obj
                }
                # only create intermediary model instance if it doesn't already exist
                if not attribute.through.objects.filter(**through_params).exists():
                    attribute.through.objects.create(**through_params)

    def handle_outgoing(self, ctx, source_obj, target_dict):
        attrs = self._attribute.split('.')
        attribute = source_obj

        for attr in attrs:
            attribute = getattr(attribute, attr, None)
            if attribute is None:
                return None

        objects = []

        # We are doing this outside of get_iterable so that subclasses can not
        # remove this override.
        if self._iterable_factory:
            iterable = self._iterable_factory(attribute)
        else:
            iterable = self.get_iterable(attribute)

        for model in iterable:
            model_resource = self._resource_class(model)
            model_dict = model_resource.get(ctx, EmptyParams())
            # only add '_id' if there is no 'resourceUri'
            if 'resourceUri' not in model_dict:
                model_dict['_id'] = model_resource.key
            objects.append(model_dict)
        target_dict[self._compute_property(ctx)] = objects

    def validate_resource(self, ctx, key, resource, source_dict_list):
        error_dict = {}
        if self.validator:
            self.validator.find_errors(error_dict, ctx, key, resource, self, source_dict_list)
        return error_dict

    def schema(self, ctx, **kwargs):
        return super(IterableField, self).schema(ctx, **kwargs)
