import logging
import unittest
import mock
from savory_pie.django.utils import Related, getLogger
from savory_pie.tests.django import mock_orm


class LoggerTestCase(unittest.TestCase):

    def test_logger_callable(self):
        with self.assertRaises(AssertionError):
            logger = getLogger()
            logger.callable('some var', logger=None)

    def test_logger_im_func(self):
        func = mock.MagicMock(return_value=None, name='logger')

        im_func = mock.MagicMock(name='im_func')

        func_code = mock.MagicMock(name='func_code')
        im_func.func_code = func_code
        func.im_func = im_func

        func_code.co_filename = 'file name'
        func_code.co_firstlineno = 23
        func_code.co_name = 'name'

        logger = mock.MagicMock()

        lg = getLogger()
        lg.callable(func, logger=logger)
        logger._log.assert_called_with(logging.DEBUG, 'file name:23 name', [], {})

    def test_logger(self):
        func = mock.MagicMock(return_value=None, name='logger', spec=['func_code'])

        func_code = mock.MagicMock(name='func_code')
        func.func_code = func_code

        func_code.co_filename = 'file name'
        func_code.co_firstlineno = 23
        func_code.co_name = 'name'

        logger = mock.MagicMock()

        lg = getLogger()
        lg.callable(func, logger=logger)
        logger._log.assert_called_with(logging.DEBUG, 'file name:23 name', [], {})

    def test_logger_alert(self):
        logger = mock.MagicMock()

        lg = getLogger()
        lg.alert('object', marker='1', logger=logger)
        bannerEdge = '1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1'

        calls = [
            mock.call(logging.DEBUG, bannerEdge, [], {}),
            mock.call(logging.DEBUG, bannerEdge, [], {}),
            mock.call(logging.DEBUG, '                                     object', [], {}),
            mock.call(logging.DEBUG, bannerEdge, [], {}),
            mock.call(logging.DEBUG, bannerEdge, [], {}),

        ]
        logger._log.assert_has_calls(calls)

    @mock.patch('savory_pie.django.utils.pprint.pformat')
    def test_pp_enabled(self, pformat):
        pformat.return_value = 'something pprinted'
        logger = mock.MagicMock()
        logger.isEnabledFor.return_value = True
        lg = getLogger()
        lg.pprint('object', logger=logger)
        logger._log.assert_called_with(logging.DEBUG, '\nsomething pprinted', [], {})

    @mock.patch('savory_pie.django.utils.pprint.pformat')
    def test_pp_dis_enabled(self, pformat):
        pformat.return_value = 'something pprinted'
        logger = mock.MagicMock()
        logger.isEnabledFor.return_value = False
        lg = getLogger()
        lg.pprint('object', logger=logger)
        self.assertFalse(logger._log.called)

    def test_logger_before_disabled(self):
        logger = mock.MagicMock()
        logger.isEnabledFor.return_value = False
        lg = getLogger()
        lg.before_queries(txt='object', logger=logger)
        self.assertFalse(logger._log.called)

    @mock.patch('savory_pie.django.utils.connection')
    def test_logger_before_queries(self, connection):
        connection.queries = [1, 2]
        logger = mock.MagicMock()
        logger.isEnabledFor.return_value = True
        lg = getLogger()
        lg.before_queries(txt='object', logger=logger)
        logger._log.assert_called_with(logging.DEBUG, 'object', [], {})
        self.assertEqual(logger._num_queries, 2)

    @mock.patch('savory_pie.django.utils.connection')
    def test_logger_before_queries_notxt(self, connection):
        connection.queries = [1, 2]
        logger = mock.MagicMock()
        logger.isEnabledFor.return_value = True
        lg = getLogger()
        lg.before_queries(logger=logger)
        self.assertFalse(logger._log.called)
        self.assertEqual(logger._num_queries, 2)

    @mock.patch('savory_pie.django.utils.connection')
    def test_logger_before_queries_disabled(self, connection):
        connection.queries = [1, 2]
        logger = mock.MagicMock()
        logger._num_queries = 0
        logger.isEnabledFor.return_value = False
        lg = getLogger()
        lg.after_queries(logger=logger)
        self.assertFalse(logger._log.called)
        self.assertEqual(logger._num_queries, 0)

    @mock.patch('savory_pie.django.utils.connection')
    def test_logger_after_queries_enabled(self, connection):
        logger = mock.MagicMock()
        logger._num_queries = 1
        qry1 = {'name': 'qry1', 'time': '1', 'sql': 'select'}
        qry2 = {'name': 'qry2', 'time': '2', 'sql': 'insert'}
        qry3 = {'name': 'qry3', 'time': '3', 'sql': 'update'}

        connection.queries = [qry1, qry2, qry3]
        logger.isEnabledFor.return_value = True

        lg = getLogger()
        lg.after_queries(obj='object', logger=logger)

        calls = [
            mock.call(logging.DEBUG, 'Database hits: 2', [], {}),
            mock.call(logging.DEBUG, 'Database hit, 2 seconds\ninsert', [], {}),
            mock.call(logging.DEBUG, 'Database hit, 3 seconds\nupdate', [], {}),
        ]
        logger._log.assert_has_calls(calls)


class RelatedTest(unittest.TestCase):
    def test_select(self):
        related = Related()

        related.select('foo')
        self.assertEqual(related._select, {
            'foo'
        })

        related.select('bar')
        self.assertEqual(related._select, {
            'foo',
            'bar'
        })

    def test_prefetch(self):
        related = Related()

        related.prefetch('foo')
        self.assertEqual(related._prefetch, {
            'foo'
        })

        related.prefetch('bar')
        self.assertEqual(related._prefetch, {
            'foo',
            'bar'
        })

    def test_sub_select(self):
        related = Related()
        sub_related = related.sub_select('foo')

        sub_related.select('bar')
        sub_related.prefetch('baz')

        self.assertEqual(related._select, {
            'foo__bar'
        })
        self.assertEqual(related._prefetch, {
            'foo__baz'
        })

    def test_sub_prefetch(self):
        related = Related()
        sub_related = related.sub_prefetch('foo')

        sub_related.select('bar')
        sub_related.prefetch('baz')

        self.assertEqual(related._select, set())
        # Because foo is assumed to have a non-one cardinality, sub-selects
        # through foo are also converted into prefetch-es.  In this case, bar.
        self.assertEqual(related._prefetch, {
            'foo__bar',
            'foo__baz'
        })

    def test_sub_prefetch_continuation(self):
        related = Related()
        sub_related = related.sub_prefetch('foo')
        sub_sub_related = sub_related.sub_select('bar')

        sub_sub_related.select('baz')

        # Because foo was prefetch, the sub-select of bar is also forced into
        # prefetch mode, so foo__bar__baz ends up being prefetched.
        self.assertEqual(related._prefetch, {
            'foo__bar__baz'
        })

    def test_empty_prepare(self):
        related = Related()

        queryset = related.prepare(mock_orm.QuerySet())

        self.assertEqual(queryset._selected, set())
        self.assertEqual(queryset._prefetched, set())

    def test_prepare(self):
        related = Related()

        related.select('foo')
        related.prefetch('bar')

        queryset = related.prepare(mock_orm.QuerySet())

        self.assertEqual(queryset._selected, {
            'foo'
        })
        self.assertEqual(queryset._prefetched, {
            'bar'
        })
