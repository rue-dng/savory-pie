from django.core.exceptions import ObjectDoesNotExist

#protocol Resource:
class Resource(object):
    resource_path = None

#   def get(self, **kwargs): dict
#   def post(self, dict)
#   def put(self, dict): Resource
#   def delete(self)
#   def get_child_resource(self, path_fragment, light): Resource or None


class APIResource(Resource):
    def __init__(self):
        self._child_resources = dict()

    def register(self, name, resource):
        self._child_resources[name] = resource
        return self

    def register_class(self, name, resource_class):
        return self.register(name, resource_class())

    def get_child_resource(self, path_fragment, light):
        return self._child_resources.get(path_fragment, None)


class QuerySetResource(Resource):
    # resource_class
    def __init__(self, queryset=None):
        self.queryset = queryset or self.resource_class.model_class.objects.all()

    def filter_queryset(self, **kwargs):
        return self.queryset.filter(**kwargs)

    def to_resource(self, model):
        return self.resource_class(model)

    def prepare(self, queryset):
        try:
            return self.resource_class.prepare(queryset)
        except KeyError:
            return queryset

    def get(self, **kwargs):
        queryset = self.prepare(self.filter_queryset(**kwargs))

        objects = []
        for model in queryset:
            objects.append(self.to_resource(model).get())

        return {
            'objects': objects
        }

    def post(self, source_dict):
        resource = self.resource_class.create_resource()
        resource.put(source_dict)
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
    published_key = ('pk', int)
    fields = []

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

    def get(self, **kwargs):
        target_dict = dict()

        for field in self.fields:
            field.handle_outgoing(self.model, target_dict)

        return target_dict

    def put(self, source_dict):
        for field in self.fields:
            field.handle_incoming(source_dict, self.model)

        self.model.save()

    def delete(self):
        self.model.delete()
