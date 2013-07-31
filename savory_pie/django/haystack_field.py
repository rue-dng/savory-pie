import json
import logging

from savory_pie.context import APIContext

from haystack import fields as haystack_fields

logger = logging.getLogger(__name__)


class HaystackField(haystack_fields.CharField):
    """
    This field can be used to store the JSON from an API call into a Haystack search database.
    It typically wouldn't be indexed (but could be if you wanted). Typical usage:

        from haystack import indexes, fields
        from savory_pie.django.fields import HaystackField

        class FooIndex(indexes.SearchIndex, indexes.Indexable):
            foo = fields.CharField(...)
            bar = fields.CharField(...)
            api = HaystackField(base_uri='/my/api/path/',
                                formatter=JSONFormatter(),
                                resource=FooResource)
    """
    def __init__(self, *args, **kwargs):
        self._formatter = kwargs.pop('formatter', None)
        self._ctx = APIContext('SAVORY_PIE_HOSTNAME', None, self._formatter)
        self._resource = kwargs.pop('resource', None)
        self.indexed = kwargs.pop('indexed', False)
        self.stored = kwargs.pop('indexed', True)
        super(HaystackField, self).__init__(*args, **kwargs)

    def prepare(self, obj):
        try:
            import cStringIO as StringIO
        except ImportError:
            import StringIO
        api_data = self._resource(obj).get(self._ctx, {})
        api_data['$stale'] = True
        if self._formatter is None:
            return json.dumps(api_data)
        else:
            output = StringIO.StringIO()
            self._formatter.write_to(api_data, output)
            return output.getvalue()
