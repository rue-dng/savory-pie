import unittest
import mock

from savory_pie.django.haystack_resource import HaystackResource
from savory_pie.tests.mock_context import mock_context


class TestHaystackResource(unittest.TestCase):
    
    def test_have_no_children(self):
        resource = HaystackResource()
        child = resource.get_child_resource(None, None)
        self.assertEqual(None, child)

    @mock.patch('savory_pie.django.haystack_resource.SearchQuerySet')
    def test_saved_field(self, SearchQuerySet):
        # Build search and result
        search_result = mock.Mock(name='search_result')
        search_query_set = SearchQuerySet.return_value
        search_query_set.models.return_value.__iter__.return_value = iter([
            search_result
        ])

        # Build a mock field
        field = mock.Mock()
        def handle_outgoing(ctx, source_obj, target_dict):
           target_dict['foo'] = 'bar' 
        field.handle_outgoing.side_effect = handle_outgoing

        class Resource(HaystackResource):
            model = mock.sentinel.model
            fields = [
                field,
            ]

        resource = Resource()
        result_list = resource.get(mock.sentinel.ctx)

        self.assertEqual(
            [{'foo': 'bar'}],
            list(result_list)
        )

        field.handle_outgoing.assert_called_with(
            mock.sentinel.ctx,
            search_result.get_stored_fields.return_value,
            {'foo': 'bar'} # This looks odd, but the value is mutated
        )
