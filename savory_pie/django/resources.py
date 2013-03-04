import urllib

from savory_pie.resources import Resource
from savory_pie.django.utils import Related

class QuerySetResource(Resource):
    """
    Resource abstract around Django QuerySets.

    Parameters:

        ``resource_class``
            type of Resource to create for a given Model in the queryset

    Typical usage...

    .. code::

        class FooResource(ModelResource):
            parent_resource_path = 'foos'
            model_class = Foo

        class FooQuerySetResource(QuerySetResource):
            resource_path = 'foos'
            resource_class = FooResource
    """
    #: optional - if set specifies the page size for data returned during a GET
    #: - defaults to None (no paging)
    page_size = None

    def __init__(self, queryset=None):
        self.queryset = queryset or self.resource_class.model_class.objects.all()

    @property
    def supports_paging(self):
        return self.page_size is not None

    def filter_queryset(self, queryset, GET):
        # TODO: Revisit filtering
        return queryset.filter(**GET)

    def slice_queryset(self, queryset, GET):
        if self.supports_paging:
            page = self.get_page(GET)
            offset = page * self.page_size
            return queryset[offset: offset + self.page_size]
        else:
            return queryset

    def get_page(self, GET):
        return int(GET.get('page', '0'))

    def build_page_uri(self, ctx, page):
        return ctx.build_resource_uri(self) + '?' + urllib.urlencode({'page': page})

    def to_resource(self, model):
        """
        Constructs a new instance of resource_class around the provided model.
        """
        resource = self.resource_class(model)

        # Normally, traversal would take care of filling in the resource_path
        # for a child resource, but this is called to create sub-resources that are
        # embedded into a larger GET.  To make sure, the resourceUri can be
        # computed for those resources, we need to make sure they have a resource_path.
        if resource.resource_path is None and self.resource_path is not None:
            resource.resource_path = self.resource_path + '/' + str(resource.key)

        return resource

    @classmethod
    def prepare(cls, ctx, related):
        cls.resource_class.prepare(ctx, related)

    def prepare_queryset(self, ctx, queryset):
        related = Related()
        self.prepare(ctx, related)
        return related.prepare(queryset)

    def get(self, ctx, **GET):
        complete_queryset = queryset = self.queryset.all()

        filtered_queryset = self.filter_queryset(complete_queryset, GET)
        sliced_queryset = self.slice_queryset(filtered_queryset, GET)
        final_queryset = self.prepare_queryset(ctx, sliced_queryset)

        objects = []
        for model in final_queryset:
            objects.append(self.to_resource(model).get(ctx))

        meta = dict()
        if self.supports_paging:
            # When paging the sliced_queryset will not contain all the objects,
            # so the count of the accumulated objects is insufficient.  In that case,
            # need to make a call queryset.count.
            count = self.filter_queryset(complete_queryset, GET).count()

            page = self.get_page(GET)
            if page > 0:
                meta['prev'] = self.build_page_uri(ctx, page - 1)

            meta['count'] = count

            if ( page + 1 ) * self.page_size < count:
                meta['next'] = self.build_page_uri(ctx, page + 1)
        else:
            # When paging is disabled the sliced_queryset is the complete queryset,
            # so the accumulated objects contains all the objects.  In this case, just
            # do a len on the accumulated objects to avoid the extra COUNT(*) query.
            meta['count'] = len(objects)

        return {
            'meta': meta,
            'objects': objects
        }

    def post(self, ctx, source_dict):
        resource = self.resource_class.create_resource()
        resource.put(ctx, source_dict)

        # If the newly created child_resource is not absolutely addressable on
        # its own, then fill in the address (assuming the QuerySetResource
        # is addressable itself.)
        if resource.resource_path is None and self.resource_path is not None:
            resource.resource_path = self.resource_path + '/' + str(resource.key)

        return resource

    def get_child_resource(self, ctx, path_fragment):
        # No need to filter or slice here, does not make sense as part of get_child_resource
        queryset = self.prepare_queryset(ctx, self.queryset)
        try:
            model = self.resource_class.get_from_queryset(queryset, path_fragment)
            return self.to_resource(model)
        except queryset.model.DoesNotExist:
            return None


class ModelResource(Resource):
    """
    Resource abstract around ModelResource.

    Typical usage...

    .. code::

        class FooResource(ModelResource):
            parent_resource_path = 'foos'
            model_class = Foo

        class FooQuerySetResource(QuerySetResource):
            resource_path = 'foos'
            resource_class = FooResource
    """
    # model_class

    #: path of parent resource - used to compute resource_path
    parent_resource_path = None

    #: tuple of (name, type) of the key property used in the resource_path
    published_key = ('pk', int)

    #: A list of Field-s that are used to determine what properties are placed
    #: into and read from dict-s being handled by get, post, and put
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
    def prepare(cls, ctx, related):
        """
        Called by QuerySetResource to add necessary select_related-s
        calls to the QuerySet.
        """
        for field in cls.fields:
            field.prepare(ctx, related)
        return related

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
    def resource_path(self, resource_path):
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
