import logging

from haystack.query import SearchQuerySet


logger = logging.getLogger(__name__)


class HaystackResource(object):

    model = None
    fields = []
    allowed_methods = ['GET']

    def get_child_resource(self, ctx, path_fragment):
        return None

    def get(self, ctx, prams):
        search_query = SearchQuerySet().models(self.model)
        q = prams['q']
        if q:
            for word in q.split():
                search_query = search_query.filter(content=unicode(word))

        return [self._format_result(ctx, result) for result in search_query]

    def _format_result(self, ctx, search_result):
        logger.debug('Formating search result %r', search_result)
        api_result = {}
        stored_fields = search_result.get_stored_fields()
        for field in self.fields:
            field.handle_outgoing(ctx, stored_fields, api_result)
        logger.debug('Formated  search result to %r', api_result)
        return api_result
