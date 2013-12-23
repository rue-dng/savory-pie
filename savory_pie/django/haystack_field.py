import json
import logging

from haystack import indexes
from haystack import fields as haystack_fields

from savory_pie.context import APIContext
from savory_pie.django.utils import Related
from rue.products.models import Product


logger = logging.getLogger(__name__)


class ResourceIndex(indexes.SearchIndex):

    def prefetch_related(self, related):
        pass

    def get_model(self):
        return self.resource_class.model_class

    def _prefetch_related(self, qs):
        related = Related()
        ctx = APIContext('', None, None)
        self.resource_class.prepare(ctx, related)
        self.prefetch_related(related)
        return related.prepare(qs)

    def index_queryset(self, using=None):
        qs = self.get_model().objects.all()
        return self._prefetch_related(qs)

    def build_queryset(self, start_date=None, end_date=None, using=None):
        return self.index_queryset(using=using)


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

        if isinstance(obj, Product) and obj.pk == 37:
            with open("/Users/mmilkin/code/rue_buildout/file_out_twoz.txt", "a") as f:
                import pprint
                pp = pprint.PrettyPrinter(depth=7)
                f.write('\n\nAPI_DATA\n')
                f.write(pp.pformat(api_data))

        if self._formatter is None:
            return json.dumps(api_data)
        else:
            output = StringIO.StringIO()
            self._formatter.write_to(api_data, output)
            return output.getvalue()
