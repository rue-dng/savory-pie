from django.db.models.fields import Field as DjangoField
from django.utils.functional import Promise

class Field(object):
    def __init__(self, DjangoField):
        self._field = DjangoField

    def schema(self):
        _field = {
            'blank': self._field.blank,
            'default': self._field.get_default(),
            'helpText': self._field.help_text,
            'nullable': self._field.null,
            'readonly': not self._field.editable,
            'unique': self._field.unique
        }
        if isinstance(_field['helpText'], Promise):
            _field['helpText'] = unicode(_field['helpText'])
        return _field

class Related(object):
    """
    Helper object that helps build related select-s and prefetch-es.
    Originally created to work around Django silliness - https://code.djangoproject.com/ticket/16855,
    but later extended to help track the related path from the root Model being selected.
    """
    def __init__(self, **kwargs):
        self._prefix = kwargs.pop('prefix', None)

        # or-s don't work want to continue to use the same empty set
        self._select = kwargs.pop('select', set())
        self._prefetch = kwargs.pop('prefetch', set())
        self._force_prefetch = kwargs.pop('force_prefetch', False)

    def translate(self, attribute):
        if self._prefix is None:
            return attribute
        else:
            return self._prefix + '__' + attribute

    def select(self, attribute):
        """
        Called to select a related attribute -- this typically translates to a
        select_related call on the final queryset.

        When select is called on a sub-Related created directly or indirectly
        through a sub_prefetch, select-s will automatically be translated into
        prefetch-es.
        """
        # If a select call is made on a Related that was created through sub_prefetch,
        # that call must be converted into prefetch because the relationship to the
        # top element will not have a cardinality of 1.
        if self._force_prefetch:
            return self.prefetch(attribute)

        self._select.add(self.translate(attribute))
        return self

    def prefetch(self, attribute):
        """
        Called to prefetch a related attribute -- this translates into a
        prefetch_related call on the final queryset.
        """
        self._prefetch.add(self.translate(attribute))
        return self

    def sub_select(self, attribute):
        """
        Creates a sub-Related through this relationship.  All calls to select or
        prefetch on the resulting sub-Related will be automatically qualified with
        {attribute}__.

        A sub-select Related acquired through a sub-prefetch Related will continue
        to translates all select-s to prefetch-es.
        """
        return Related(
            prefix=self.translate(attribute),
            select=self._select,
            prefetch=self._prefetch,
            force_prefetch=self._force_prefetch
        )

    def sub_prefetch(self, attribute):
        """
        Creates a sub-Related through this relationship.  All calls to select or
        prefetch on the resulting sub-Related will be automatically qualified with
        {attribute}__.

        Furthermore, all select-s on the sub-related will be translated into
        prefetch-es because they will be read indirectly through a many relationship.
        """
        return Related(
            prefix=self.translate(attribute),
            select=self._select,
            prefetch=self._prefetch,
            force_prefetch=True
        )

    def prepare(self, queryset):
        """
        Should be called after all select and prefetch calls have been made to
        applied the accumulated confiugration to a QuerySet.
        """
        if self._select:
            queryset = queryset.select_related(*self._select)

        if self._prefetch:
            queryset = queryset.prefetch_related(*self._prefetch)

        return queryset

