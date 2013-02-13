from django.core.exceptions import ObjectDoesNotExist


class Resource(object):
    """
    Base object for defining resources.

    Properties...
    resource_path - defaults to None
        Internal path (from root of the resource tre to this Resource).
        If not set, this is auto-filled during Resource traversal;
        however, if you wish for a Resource to always be addressable,
        resource_path should be set at construction.

    allowed_methods - defaults to set of available methods based on
        presence of the optional methods - get, post, put, etc.

        Can be overridden with a static set or dynamic property to
        create access controls.
    """
    resource_path = None

    @property
    def allowed_methods(self):
        allowed_methods = set()

        for http_method in set('GET', 'POST', 'PUT', 'DELETE'):
            obj_method = http_method.lower()
            try:
                getattr(self, obj_method)
                allowed_methods.add(http_method)
            except AttributeError:
                pass

        return allowed_methods

    # def get(self, ctx, **kwargs):
        """
        Optional method that is called during a GET request.

        get is provided an APIContext and an optional set of kwargs that include the
        query string params.

        Returns a dict of data to be serialized to the requested format.
        """

    # def post(self, ctx, dict):
        """
        Optional method that is called during a POST request.

        post is provided with a dict representing the deserialized representation of
        the body content.

        Returns a new Resource
        """

    # def put(self, ctx, dict):
        """
        Optional method that is called during a PUT request.

        put is provided with a dict representing the deserialized representation of
        the body content.
        """

    # def delete(self, ctx):
        """
        Optional method that is called during a DELETE request.
        """

    def get_child_resource(self, ctx, path_fragment):
        return None

class APIResource(Resource):
    def __init__(self, resource_path=''):
        self.resource_path = resource_path
        self._child_resources = dict()

    def register(self, resource):
        """
        Register a resource into the API.  The Resource must
        have a first-level resource_path already set.
        """
        if resource.resource_path.find('/') != -1:
            raise ValueError, 'resource_path should be top-level'

        self._child_resources[resource.resource_path] = resource
        return self

    def register_class(self, resource_class):
        """
        Register a resource class into the API.  The constructed
        Resource must have a first-level resource_path set after
        construction.
        """
        return self.register(resource_class())

    def get_child_resource(self, ctx, path_fragment):
        return self._child_resources.get(path_fragment, None)


class QuerySetResource(Resource):
    """
    Resource abstract around Django QuerySets.
    resource_class - type of Resource to create for a given Model in the queryset.

    Typical usage...
    class FooResource(ModelResource):
        parent_resource_path = 'foos'
        model_class = Foo

    class FooQuerySetResource(QuerySetResource):
        resource_path = 'foos'
        resource_class = FooResource
    """
    # resource_class

    def __init__(self, queryset=None):
        self.queryset = queryset or self.resource_class.model_class.objects.all()

    def filter_queryset(self, **kwargs):
        return self.queryset.filter(**kwargs)

    def to_resource(self, model):
        """
        Constructs a new instance of resource_class around the provided model.
        """
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
    """
    Resource abstract around ModelResource.

    parent_resource_path - path of parent resource - used to compute resource_path
    resource_class - type of Resource to create for a given Model in the queryset.
    published_key - tuple of (name, type) of the key property used in the resource_path
        - defaults to ('pk', int)
    fields - a list of Field-s that are used to determine what properties are placed
        into and read from dict-s being handled by get, post, and put

    Typical usage...
    class FooResource(ModelResource):
        parent_resource_path = 'foos'
        model_class = Foo

    class FooQuerySetResource(QuerySetResource):
        resource_path = 'foos'
        resource_class = FooResource
    """
    # model_class
    parent_resource_path = None
    published_key = ('pk', int)
    fields = []

    _resource_path = None

    @classmethod
    def get_from_queryset(cls, queryset, path_fragment):
        """
        Called by containing QuerySetResource to filter the QuerySet down
        to a single item -- represented by this ModelResource
        """
        attr, type_ = cls.published_key

        kwargs = dict()
        kwargs[attr] = type_(path_fragment)
        return queryset.get(**kwargs)

    @classmethod
    def create_resource(cls):
        """
        Creates a new ModelResource around a new model_class instance
        """
        return cls(cls.model_class())

    @classmethod
    def prepare(cls, queryset):
        """
        Called by QuerySetResource to add necessary select_related-s
        calls to the QuerySet.
        """
        prepared_queryset = queryset
        for field in cls.fields:
            prepared_queryset = field.prepare(prepared_queryset)
        return prepared_queryset

    def __init__(self, model):
        self.model = model

    @property
    def key(self):
        """
        Provides the value of the published_key of this ModelResource.
        May fail if the ModelResource was constructed around an uncommitted Model.
        """
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
            target_dict['resourceUri'] = ctx.build_resource_uri(self)

        return target_dict

    def put(self, ctx, source_dict):
        for field in self.fields:
            field.handle_incoming(ctx, source_dict, self.model)

        self.model.save()

    def delete(self, ctx):
        self.model.delete()
