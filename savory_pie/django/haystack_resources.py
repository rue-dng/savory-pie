import haystack.inputs

from haystack.query import SearchQuerySet

from savory_pie.resources import Resource
from savory_pie.helpers import _hash_string


class HaystackSearchResource(Resource):
    """
    The HaystackSearchResource returns model API details directly from the
    search index. This is much faster than making the DB queries, but can
    result in old data being returned.
    """
    model_class = None

    def _filter_qs(self, params, qs):
        return qs

    def get(self, ctx, params):
        ctx.streaming_response = True
        qs = SearchQuerySet().models(self.model_class)
        if 'q' in params:
            qs = qs.filter(content=haystack.inputs.AutoQuery(params.get('q')))
        qs = self._filter_qs(params, qs)

        def result(qs):
            # Use a result generator so we can avoid string concatenation
            count = qs.count()
            last = count - 1
            yield '{"meta":{"count":'
            yield str(count)
            yield '},"objects":['
            for i, result in enumerate(qs):
                # TODO document this ugliness
                apistring = result.get_stored_fields()['api']
                apistring = apistring.replace('SAVORY_PIE_HOSTNAME', ctx.base_uri)

                if apistring.endswith('}'):
                    apistring = '{},"$hash":"{}"}}'.format(
                        apistring[:-1],
                        _hash_string(apistring)
                    )
                yield apistring
                if i != last:
                    yield ','
            yield ']}'
        return result(qs)
