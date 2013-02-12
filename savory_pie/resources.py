from django.core.exceptions import ObjectDoesNotExist

class Resource(object):
    resource_path = None

    def get_child_resource(self, path_fragment):
        return None
#   def get(self, ctx, **kwargs): dict
#   def post(self, ctx, dict)
#   def put(self, ctx, dict): Resource
#   def delete(self, ctx)


class APIResource(Resource):
    def __init__(self, resource_path=''):
        self.resource_path = resource_path
        self._child_resources = dict()

    def register(self, resource):
        if resource.resource_path.find('/') != -1:
            raise ValueError, 'resource_path should be top-level'

        self._child_resources[resource.resource_path] = resource
        return self

    def register_class(self, resource_class):
        return self.register(resource_class())

    def get_child_resource(self, path_fragment):
        return self._child_resources.get(path_fragment, None)


class QuerySetResource(Resource):
    # resource_class

    def __init__(self, queryset=None):
        self.queryset = queryset or self.resource_class.model_class.objects.all()

    def filter_queryset(self, **kwargs):
        return self.queryset.filter(**kwargs)

    def to_resource(self, model):
        resource = self.resource_class(model)

        if self.resource_path is not None and resource.resource_path is None:
            resource.resource_path = self.resource_path + '/' + str(resource.key)

        return resource

    def prepare(self, queryset):
        try:
            return self.resource_class.prepare(queryset)
        except KeyError:
            return queryset

    def get(self, ctx, **kwargs):
        queryset = self.prepare(self.filter_queryset(**kwargs))

        objects = []
        for model in queryset:
            objects.append(self.to_resource(model).get(ctx))

        return {
            'objects': objects
        }

    def post(self, ctx, source_dict):
        resource = self.resource_class.create_resource()
        resource.put(ctx, source_dict)

        if resource.resource_path is None:
            resource.resource_path = self.resource_path + '/' + str(resource.key)

        return resource

    def get_child_resource(self, path_fragment):
        try:
            model = self.resource_class.get_from_queryset(
                self.prepare(self.queryset),
                path_fragment
            )
            return self.to_resource(model)
        except ObjectDoesNotExist:
            return None


class ModelResource(Resource):
    # model_class
    parent_resource_path = None
    published_key = ('pk', int)
    fields = []

    _resource_path = None

    @classmethod
    def get_from_queryset(cls, queryset, path_fragment):
        attr, type_ = cls.published_key

        kwargs = dict()
        kwargs[attr] = type_(path_fragment)
        return queryset.get(**kwargs)

    @classmethod
    def create_resource(cls):
        return cls(cls.model_class())

    @classmethod
    def prepare(cls, queryset):
        prepared_queryset = queryset
        for field in cls.fields:
            prepared_queryset = field.prepare(prepared_queryset)
        return prepared_queryset

    def __init__(self, model):
        self.model = model

    @property
    def key(self):
        attr, type_ = self.published_key
        return str(getattr(self.model, attr))

    @property
    def resource_path(self):
        if self._resource_path is not None:
            return self._resource_path
        elif self.parent_resource_path is not None:
            return self.parent_resource_path + '/' + str(self.key)
        else:
            return None

    @resource_path.setter
    def set_resource_path(self, resource_path):
        # TODO: Sanity checks that path is bound properly
        self._resource_path = resource_path


    def get(self, ctx, **kwargs):
        target_dict = dict()

        for field in self.fields:
            field.handle_outgoing(ctx, self.model, target_dict)

        if self.resource_path is not None:
            target_dict['resourceUri'] = ctx.build_absolute_uri(self)

        return target_dict

    def put(self, ctx, source_dict):
        for field in self.fields:
            field.handle_incoming(ctx, source_dict, self.model)

        self.model.save()

    def delete(self, ctx):
        self.model.delete()
