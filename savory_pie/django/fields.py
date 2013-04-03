import collections
import logging
import django.core.exceptions
from django.utils.functional import Promise
from django.db.models.fields import FieldDoesNotExist
from savory_pie import fields as base_fields

logger = logging.getLogger(__name__)
print 'logging with name {0}'.format(__name__)

class DjangoField(base_fields.Field):
    def schema(self, ctx, **kwargs):
        model = kwargs['model']
        field_name = (model._meta.pk.name if self.name == 'pk' else self.name)
        self._field = None
        try:
            self._field = model._meta.get_field(field_name)
        except:
            # probably only for m2m fields
            try:
                self._field = model._meta.get_field_by_name(field_name)[0].field
            except FieldDoesNotExist:
                self._field = None

        schema = super(DjangoField, self).schema(**kwargs)
        if isinstance(self.validator, collections.Iterable):
            schema['validators'] = [validator.to_schema() for validator in self.validator]
        else:
            schema['validators'] = [self.validator.to_schema()]

        if self._field:
            _schema = {
                'blank': self._field.blank,
                'default': ctx.formatter.to_api_value(type(self._field.get_default()), self._field.get_default()),
                'helpText': self._field.help_text,
                'nullable': self._field.null,
                'readonly': not self._field.editable,
                'unique': self._field.unique
            }
            if self._field.choices:
                _schema['choices'] = self._field.choices
            if isinstance(_schema['helpText'], Promise):
                _schema['helpText'] = unicode(_schema['helpText'])
        else:
            _schema = {}

        return dict(schema.items() + _schema.items())


class AttributeField(base_fields.AttributeField, DjangoField):
    """
    Django extension of the basic AttributeField that adds support for optimized select_related
    or prefetch_related calls.

    Parameters:
            :class:`savory_pie.fields.AttributeField`

            ``use_prefetch``
                optional -- tells the attribute field to use
                prefetch_related rather than a select_related.  Defaults to false.

                There are two reasons you might need to do this...

                - select_related will not work when the foreign key allows null.
                - select_related will not work when the foreign key is a GenericForeignKey.

                See https://docs.djangoproject.com/en/dev/ref/models/querysets/

                This parameter is meaningless for top-level attributes.
    """
    def __init__(self, *args, **kwargs):
        self.pre_save = True
        self._use_prefetch = kwargs.pop('use_prefetch', False)
        super(AttributeField, self).__init__(*args, **kwargs)

    def prepare(self, ctx, related):
        related_attr = '__'.join(self._attrs[:-1])
        if related_attr:
            if self._use_prefetch:
                related.prefetch(related_attr)
            else:
                related.select(related_attr)

    def filter_by_item(self, ctx, filter_args, source_dict):
        filter_args[self._full_attribute] = source_dict[self._compute_property(ctx)]


class URIResourceField(base_fields.URIResourceField, DjangoField):
    """
    Django extension of the basic URIResourceField that adds support for optimized
    select_related or prefetch_related calls.

    Parameters:
            :class:`savory_pie.fields.URIResourceField`

            ``use_prefetch``
                optional -- tells the attribute field to use
                prefetch_related rather than a select_related.  Defaults to false.

                There are two reasons you might need to do this...

                - select_related will not work when the foreign key allows null.
                - select_related will not work when the foreign key is a GenericForeignKey.

                See https://docs.djangoproject.com/en/dev/ref/models/querysets/

                This parameter is meaningless for top-level attributes.
    """
    def __init__(self, *args, **kwargs):
        self._use_prefetch = kwargs.pop('use_prefetch', False)
        self.pre_save = True
        super(URIResourceField, self).__init__(*args, **kwargs)


    def prepare(self, ctx, related):
        if self._use_prefetch:
            related.sub_prefetch(self._attribute)
        else:
            related.sub_select(self._attribute)


class SubModelResourceField(base_fields.SubObjectResourceField, DjangoField):
    """
    Django extension of the basic SubObjectResourceField that adds support for
    optimized select_related or prefetch_related calls.

        Parameters:
            :class:`savory_pie.fields.SubModelResourceField`

            ``use_prefetch``
                optional -- tells the sub-model resource field to use
                prefetch_related rather than a select_related.  Defaults to false.

                There are two reasons you might need to do this...

                - select_related will not work when the foreign key allows null.
                - select_related will not work when the foreign key is a GenericForeignKey.

                See https://docs.djangoproject.com/en/dev/ref/models/querysets/
    """
    def __init__(self, *args, **kwargs):
        self._use_prefetch = kwargs.pop('use_prefetch', False)
        super(SubModelResourceField, self).__init__(*args, **kwargs)

    def prepare(self, ctx, related):
        if self._use_prefetch:
            related.prefetch(self._attribute)
            self._resource_class.prepare(ctx, related.sub_prefetch(self._attribute))
        else:
            related.select(self._attribute)
            self._resource_class.prepare(ctx, related.sub_select(self._attribute))

    def schema(self, ctx, **kwargs):
        kwargs = dict(kwargs.items() + {'schema': {'type': 'related', 'relatedType': 'to_one'}}.items())
        return super(SubModelResourceField, self).schema(ctx, **kwargs)

    def get_subresource(self, ctx, source_dict, target_obj):
        sub_source_dict = source_dict[self._compute_property(ctx)]
        try:
            # Look at non-null FK
            sub_resource = super(SubModelResourceField, self).get_subresource(
                ctx,
                source_dict,
                target_obj
            )
        except django.core.exceptions.ObjectDoesNotExist:
            # Search by the source dict
            sub_resource = self._resource_class.get_by_source_dict(ctx, sub_source_dict)

        # Make sure the new model is attached
        if hasattr(sub_resource, 'model'):
            setattr(target_obj, self._attribute, sub_resource.model)
        return sub_resource

    def get_submodel(self, ctx, source_object):
        try:
            # Look at non-null FK
            sub_model = super(SubModelResourceField, self).get_submodel(
                ctx,
                source_object
            )
        except django.core.exceptions.ObjectDoesNotExist:
            sub_model = None

        return sub_model

    @property
    def pre_save(self):
        '''
        This is to figure if we need to pre_save the foreign key or not.
        If Model A has foreign key to Model B, do everything normal
        If Model B has foreign key to Model A, you need to save Model A first before setting value on Model B
        @return: a Boolean variable used in ModelResources' put
        '''

        try:
            attribute_name = self._field.related.field.name
            attribute = getattr(self._resource_class.model_class, attribute_name)
            if isinstance(attribute, django.db.models.fields.related.ReverseSingleRelatedObjectDescriptor):
                logger.debug('Setting pre_save to false with attribute %s and attribute_name %s', self._attribute, attribute_name)
                return False
        except AttributeError:
            logger.debug('Setting pre_save to True with attribute %s', self._attribute)
            return True


class RelatedManagerField(base_fields.IterableField, DjangoField):
    """
    Django extension of the basic IterableField that adds support for
    optimized select_related or prefetch_related calls.

        Parameters:
            :class:`savory_pie.fields.IterableField`
    """
    def __init__(self, *args, **kwargs):
        '''
        This is to figure out if we need to pre_save the many to many field or not.
        In this case, we always want the related model to save first, before we save ourselves.
        @return: a Boolean variable used in ModelResources' put
        '''
        self.pre_save = False
        super(RelatedManagerField, self).__init__(*args, **kwargs)

    def get_iterable(self, value):
        return value.all()

    def prepare(self, ctx, related):
        attrs = self._attribute.replace('.', '__')
        related.prefetch(attrs)
        self._resource_class.prepare(ctx, related.sub_prefetch(attrs))

    def schema(self, ctx, **kwargs):
        kwargs = dict(kwargs.items() + {'schema': {'type': 'related', 'relatedType': 'to_many'}}.items())
        return super(RelatedManagerField, self).schema(ctx, **kwargs)
