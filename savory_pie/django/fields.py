import django.core.exceptions

from savory_pie import fields as base_fields


class AttributeField(base_fields.AttributeField):
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


class URIResourceField(base_fields.URIResourceField):
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

        super(URIResourceField, self).__init__(*args, **kwargs)


    def prepare(self, ctx, related):
        if self._use_prefetch:
            related.sub_prefetch(self._attribute)
        else:
            related.sub_select(self._attribute)


class SubModelResourceField(base_fields.SubObjectResourceField):
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

    @base_fields.read_only_noop
    def handle_incoming(self, ctx, source_dict, target_obj):
        # CLEAN ME UP
        try:
            sub_model = getattr(target_obj, self._attribute)
        except django.core.exceptions.ObjectDoesNotExist:
            sub_model = None

        sub_source_dict = source_dict[self._compute_property(ctx)]

        if sub_model is None:
            sub_resource = self._resource_class.get_by_source_dict(ctx, sub_source_dict)
            if not sub_resource:
                sub_resource = self._resource_class.create_resource()
        else:
            sub_resource = self._resource_class(sub_model)

        sub_resource.put(ctx, sub_source_dict)
        # Must be after the save on the sub_model
        setattr(target_obj, self._attribute, sub_resource.model)


class RelatedManagerField(base_fields.IterableField):
    """
    Django extension of the basic IterableField that adds support for
    optimized select_related or prefetch_related calls.

        Parameters:
            :class:`savory_pie.fields.IterableField`
    """

    def get_iterable(self, value):
        return value.all()

    def prepare(self, ctx, related):
        related.prefetch(self._attribute)
        self._resource_class.prepare(ctx, related.sub_prefetch(self._attribute))

