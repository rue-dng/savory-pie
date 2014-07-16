import logging
import pprint
import sys
import traceback

from django.db import connection


def getLogger(name=None, stream=None):
    if name is None:
        name = __name__

    logger = logging.getLogger(name)
    formatter = logging.Formatter("[%(funcName)s: %(filename)s:%(lineno)d] %(message)s")
    handler = logging.StreamHandler(stream=stream or sys.stderr)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    def logger_callable(f, logger=logger):
        assert callable(f)
        if hasattr(f, 'im_func'):
            f = f.im_func
        fc = f.func_code
        info = '{0}:{1} {2}'.format(fc.co_filename, fc.co_firstlineno, fc.co_name)
        logger._log(logging.DEBUG, info, [], {})
    logger.callable = logger_callable

    def logger_alert(obj, marker='*', logger=logger):
        if logger.isEnabledFor(logging.DEBUG):
            bannerEdge = ' '.join(40 * [marker])
            objStr = str(obj)
            logger._log(logging.DEBUG, bannerEdge, [], {})
            logger._log(logging.DEBUG, bannerEdge, [], {})
            logger._log(logging.DEBUG, ((40 - len(objStr) / 2) * ' ') + objStr, [], {})
            logger._log(logging.DEBUG, bannerEdge, [], {})
            logger._log(logging.DEBUG, bannerEdge, [], {})
    logger.alert = logger_alert

    def logger_pprint(obj, logger=logger):
        if logger.isEnabledFor(logging.DEBUG):
            logger._log(logging.DEBUG, '\n' + pprint.pformat(obj), [], {})
    logger.pprint = logger_pprint

    def logger_tb(logger=logger):
        if logger.isEnabledFor(logging.DEBUG):
            message = ''.join(traceback.format_stack())
            logger._log(logging.DEBUG, '\n' + message, [], {})
    logger.tb = logger_tb

    # show database queries
    def logger_before_queries(txt=None, logger=logger):
        if logger.isEnabledFor(logging.DEBUG):
            if txt is not None:
                logger._log(logging.DEBUG, txt, [], {})
            logger._num_queries = len(connection.queries)

    def logger_after_queries(obj=None, logger=logger):
        if logger.isEnabledFor(logging.DEBUG):
            queries = connection.queries[logger._num_queries:]
            if len(queries) > 0:
                logger._log(logging.DEBUG, 'Database hits: {0}'.format(len(queries)), [], {})
                for query in queries:
                    about = 'Database hit, {0} seconds\n'.format(query['time'])
                    logger._log(logging.DEBUG, about + query['sql'], [], {})
            if obj is not None:
                logger._log(logging.DEBUG, '\n' + pprint.pformat(obj), [], {})
            logger._num_queries = len(connection.queries)

    logger.before_queries = logger_before_queries
    logger.after_queries = logger_after_queries
    return logger

logger = getLogger()


class Related(object):
    """
    Helper object that helps build related select-s and prefetch-es.
    Originally created to work around Django silliness - https://code.djangoproject.com/ticket/16855,
    but later extended to help track the related path from the root Model being selected.
    """
    def __init__(self, prefix=None, select=None, prefetch=None, force_prefetch=False):
        self._prefix = prefix
        self._select = select if select is not None else set()
        self._prefetch = prefetch if prefetch is not None else set()
        self._annotate = []
        self._force_prefetch = force_prefetch

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

    def annotate(self, aggregate, *args, **kwargs):
        """
        Adds an annotation to the current query set. Annotations are always
        added to the end of the query set so all filters will be applied.

        Example usage:
            ``related.aggregate(Count, 'book')``
        """
        self._annotate.append(aggregate(*args, **kwargs))

    def prepare(self, queryset):
        """
        Should be called after all select and prefetch calls have been made to
        applied the accumulated confiugration to a QuerySet.
        """
        if self._select:
            queryset = queryset.select_related(*self._select)

        if self._prefetch:
            queryset = queryset.prefetch_related(*self._prefetch)

        if self._annotate:
            queryset = queryset.annotate(*self._annotate)

        return queryset
