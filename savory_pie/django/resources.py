from collections import OrderedDict
import urllib
import logging

import django.core.exceptions
import dirty_bits

from savory_pie.resources import EmptyParams, Resource
from savory_pie.django.utils import Related
from savory_pie.django.fields import ReverseField
from savory_pie.django.validators import ValidationError, validate
from savory_pie.helpers import get_sha1
from savory_pie.errors import SavoryPieError

logger = logging.getLogger(__name__)


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
            resource_class = FooResource
    """
    #: optional - if set specifies the page size for data returned during a GET
    #: - defaults to None (no paging)
    page_size = None
    filters = []

    #Setup so that by default we will allow Unfiltered Queries
    #TODO: We need to swap this to False eventually and whitelist. However to limit halo, a blacklist will be used.
    allow_unfiltered_query = True

    def __init__(self, queryset=None):
        if queryset is not None:
            self.queryset = queryset
        else:
            self.queryset = self.resource_class.model_class.objects.all()

    @property
    def supports_paging(self):
        return self.page_size is not None

    @property
    def resource_path(self):
        return self.resource_class.parent_resource_path

    def filter_queryset(self, ctx, params, queryset):
        for filter in self.filters:
            queryset = filter.filter(ctx, params, queryset)

        # The extra filter call exists to keep a test passing
        return queryset.filter()

    def slice_queryset(self, ctx, params, queryset):
        if self.supports_paging:
            page = params.get_as('page', int, 0)
            offset = page * self.page_size
            return queryset[offset: offset + self.page_size]
        else:
            return queryset

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

    def get(self, ctx, params):
        if not self.allow_unfiltered_query and not params.keys():
            raise SavoryPieError(
                'Request must be filtered, will not return all.  Acceptable filters are: {0}'.format([filter.name for filter in self.filters])
            )

        complete_queryset = self.queryset.all().distinct()

        filtered_queryset = self.filter_queryset(ctx, params, complete_queryset)
        sliced_queryset = self.slice_queryset(ctx, params, filtered_queryset)

        # prepare must be last for optimization to be respected by Django.
        final_queryset = self.prepare_queryset(ctx, sliced_queryset)

        objects = []
        for model in final_queryset:
            model_json = self.to_resource(model).get(ctx, EmptyParams())
            model_json['$hash'] = get_sha1(ctx, model_json)
            objects.append(model_json)

        meta = dict()
        if self.supports_paging:
            # When paging the sliced_queryset will not contain all the objects,
            # so the count of the accumulated objects is insufficient.  In that case,
            # need to make a call to queryset.count.
            count = filtered_queryset.count()

            page = params.get_as('page', int, 0)
            if page > 0:
                meta['prev'] = self.build_page_uri(ctx, page - 1)

            meta['count'] = count

            if (page + 1) * self.page_size < count:
                meta['next'] = self.build_page_uri(ctx, page + 1)
        else:
            # When paging is disabled the sliced_queryset is the complete queryset,
            # so the accumulated objects contains all the objects.  In this case, just
            # do a len on the accumulated objects to avoid the extra COUNT(*) query.
            meta['count'] = len(objects)

        # add meta-level resourceUri to QuerySet response
        if self.resource_path is not None:
            meta['resourceUri'] = ctx.build_resource_uri(self)

        return {
            'meta': meta,
            'objects': objects
        }

    def post(self, ctx, source_dict):
        resource = self.resource_class.create_resource()
        if filter(lambda field: isinstance(field, ReverseField), resource.fields):
            raise ValidationError(resource, {'do not post a resource with a ReverseField':
                                             type(resource).__name__})
        with ctx.target(resource.model):
            resource.put(ctx, source_dict)

        # If the newly created child_resource is not absolutely addressable on
        # its own, then fill in the address (assuming the QuerySetResource
        # is addressable itself.)
        if resource.resource_path is None and self.resource_path is not None:
            resource.resource_path = self.resource_path + '/' + str(resource.key)

        return resource

    def get_child_resource(self, ctx, path_fragment):
        if path_fragment == 'schema':
            return SchemaResource(self.resource_class)

        # No need to filter or slice here, does not make sense as part of get_child_resource
        queryset = self.prepare_queryset(ctx, self.queryset)
        try:
            model = self.resource_class.get_from_queryset(queryset, path_fragment)
            return self.to_resource(model)
        except queryset.model.DoesNotExist:
            return None


class DirtyInitializerMetaClass(type):

    def __new__(cls, name, bases, dct):
        model_class = dct.get('model_class', None)
        if model_class:
            dirty_bits.register(model_class)
        else:
            for base in bases:
                model_class = getattr(base, 'model_class', None)
                if model_class:
                    dirty_bits.register(model_class)
                    break
        return type.__new__(cls, name, bases, dct)


class ModelResource(Resource):
    """
    Resource abstract around ModelResource.

    Typical usage...

    .. code::

        class FooResource(ModelResource):
            parent_resource_path = 'foos'
            model_class = Foo

        class FooQuerySetResource(QuerySetResource):
            resource_class = FooResource
    """
    # Must have a metaclass to instantiate dirty checking
    __metaclass__ = DirtyInitializerMetaClass

    #: path of parent resource - used to compute resource_path
    parent_resource_path = None

    #: tuple of (name, type) of the key property used in the resource_path
    published_key = ('pk', int)

    #: A list of Field-s that are used to determine what properties are placed
    #: into and read from dict-s being handled by get, post, and put
    fields = []

    #: A list of Validator-s that are used to check data consistency and
    #: integrity on a model.
    validators = []

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
            try:
                prepare = field.prepare
            except AttributeError:
                pass
            else:
                prepare(ctx, related)
        return related

    @classmethod
    def get_by_source_dict(cls, ctx, source_dict):
        filters = {}
        for field in cls.fields:
            try:
                filter_by_item = field.filter_by_item
            except AttributeError:
                pass
            else:
                filter_by_item(ctx, filters, source_dict)

        try:
            model = cls.model_class.objects.filter(**filters).get()
        except django.core.exceptions.ObjectDoesNotExist:
            return None
        else:
            return cls(model)

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

    def get(self, ctx, params):
        target_dict = OrderedDict()

        for field in self.fields:
            field.handle_outgoing(ctx, self.model, target_dict)

        if self.resource_path is not None:
            target_dict['resourceUri'] = ctx.build_resource_uri(self)

        return target_dict

    def _set_pre_save_fields(self, ctx, source_dict):
        for field in self.fields:
            try:
                pre_save = field.pre_save
            except AttributeError:
                field.handle_incoming(ctx, source_dict, self.model)
            else:
                if pre_save(self.model):
                    field.handle_incoming(ctx, source_dict, self.model)

    def _set_post_save_fields(self, ctx, source_dict):
        for field in self.fields:
            try:
                pre_save = field.pre_save
            except AttributeError:
                pass
            else:
                if not pre_save(self.model):
                    field.handle_incoming(ctx, source_dict, self.model)

    def _save(self):
        if self.model.is_dirty():
            self.model.save()

        for field in self.fields:
            try:
                save = field.save
            except AttributeError:
                pass
            else:
                save(self.model)

    def put(self, ctx, source_dict, save=True, skip_validation=False):
        '''
        This is where we respect the 'pre_save' flag on each field.
        If pre_save is true, then we set the field value, before calling save.
        If not, call save first, before setting the field value, this is for the
        many-to-many relationship.
        '''
        if not source_dict:
            return

        if not skip_validation:
            errors = validate(ctx, self.__class__.__name__, self, source_dict)
            if errors:
                logger.debug(errors)
                raise ValidationError(self, errors)

        try:
            self._set_pre_save_fields(ctx, source_dict)
        except TypeError, e:
            import traceback
            for L in traceback.format_exc().splitlines():
                logger.debug(L)
            raise ValidationError(self, {'invalidFieldData': e.message})

        if save:
            self._save()
            logger.debug('save succeeded for %s' % self)

        self._set_post_save_fields(ctx, source_dict)
        logger.debug('put succeeded for %s' % self)

    def delete(self, ctx):
        self.model.delete()

    @classmethod
    def _validator_schema(cls):
        return [validator.to_schema() for validator in cls.validators]


class SchemaResource(Resource):
    def __init__(self, model_resource):
        self.__resource = model_resource

    @property
    def allowed_methods(self):
        return self.__resource(self.__resource.model_class).allowed_methods

    def get(self, ctx, params=None, **kwargs):
        schema = {
            'allowedDetailHttpMethods': [m.lower() for m in self.allowed_methods],
            'allowedListHttpMethods': [m.lower() for m in self.allowed_methods],
            'defaultFormat': getattr(self.__resource, 'default_format', 'application/json'),
            'defaultLimit': getattr(self.__resource, 'default_limit', 0),
            'filtering': getattr(self.__resource, 'filtering', {}),
            'ordering': getattr(self.__resource, 'ordering', []),
            'validators': self.__resource._validator_schema(),
            'resourceUri': ctx.build_resource_uri(self),
            'fields': {},
        }
        for resource_field in self.__resource.fields:
            try:
                field_name = ctx.formatter.convert_to_public_property(resource_field.name)
                schema['fields'][field_name] = resource_field.schema(ctx, model=self.__resource.model_class)
            except AttributeError:
                pass
        return schema
