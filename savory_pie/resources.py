#protocol Resource:
#    def get(self, **kwargs): dict
#    def post(self, dict):
#    def put(self, dict): resource
#    def delete(self)
#    def get_child_resource(self, path_fragment): resource or None

class QuerySetResource(object):
    # resource_class
    # model_class
    def __init__(self, queryset=None):
        self.queryset = queryset or self.model_class.objects.all()

    def filter_queryset(self, **kwargs):
        print 'filter_queryset', self.queryset
        return self.queryset.filter(**kwargs)

    def to_resource(self, model):
        return self.resource_class(model)

    def create_resource(self):
        return self.resource_class(self.model_class())

    def prepare(self, queryset):
        print 'prepare', queryset
        try:
            prepare = getattr(self.resource_class, 'prepare')
            queryset = prepare(queryset)
            print 'post prepare', queryset
            return queryset
        except KeyError:
            return queryset

    def get(self, **kwargs):
        queryset = self.prepare(self.filter_queryset(**kwargs))
        print 'get', queryset

        objects = []
        for model in queryset:
            objects.append(self.to_resource(model).get())

        return {
            'objects': objects
        }

    def post(self, source_dict):
        resource = self.create_resource()
        resource.put(source_dict)
        return resource


class ModelResource(object):
    fields = []

    def __init__(self, model):
        self.model = model

    @classmethod
    def prepare(cls, queryset):
        prepared_queryset = queryset
        for field in cls.fields:
            prepared_queryset = field.prepare(prepared_queryset)
        return prepared_queryset

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