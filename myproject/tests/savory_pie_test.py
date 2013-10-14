from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from django.utils.unittest import skip
from django.utils.unittest.case import skipIf
from django.core.management import call_command

from myproject import models

import json

DEBUG = True


class DumbTest(TestCase):

    def setUp(self):
        call_command('add_test_data')

    def tearDown(self):
        models.Author.objects.all().delete()
        models.Book.objects.all().delete()
        models.Shelf.objects.all().delete()
        models.AuthorBook.objects.all().delete()

    def fetch(self, url):
        resp = self.client.get(url)
        book = json.loads(resp.book)
        if DEBUG:
            if book.has_key('error'):
                import sys
                sys.stderr.write(book['error'])
        return book

    def test_basic(self):
        book = self.fetch('/api/authorbook')
        meta = book['meta']
        self.assertEqual(2, meta['count'])
        zc = book['objects'][0]
        self.assertTrue('/api/authorbook/' in zc['resourceUri'])
        self.assertEqual('A Tree Grows in Brooklyn', zc['book']['title'])
        self.assertEqual('abcd', zc['author']['name'])
        self.assertEqual('stuv', zc['shelf']['name'])
        zc = book['objects'][1]
        self.assertTrue('/api/authorbook/' in zc['resourceUri'])
        self.assertEqual('The Sun Also Rises', zc['book']['title'])
        self.assertEqual('efgh', zc['author']['name'])
        self.assertEqual('wxyz', zc['shelf']['name'])

    def test_standard_filter(self):
        book = self.fetch('/api/authorbook?authorOne=')
        # import sys, pprint; print >> sys.stderr; pprint.pprint(book, stream=sys.stderr)
        meta = book['meta']
        self.assertEqual(1, meta['count'])
        zc = book['objects'][0]
        self.assertTrue('/api/authorbook/' in zc['resourceUri'])
        self.assertEqual('A Tree Grows in Brooklyn', zc['book']['title'])
        self.assertEqual('abcd', zc['author']['name'])
        self.assertEqual('stuv', zc['shelf']['name'])

    def test_parameterized_filter(self):
        book = self.fetch('/api/authorbook?author=1')
        meta = book['meta']
        self.assertEqual(1, meta['count'])
        zc = book['objects'][0]
        self.assertTrue('/api/authorbook/' in zc['resourceUri'])
        self.assertEqual('A Tree Grows in Brooklyn', zc['book']['title'])
        self.assertEqual('abcd', zc['author']['name'])
        self.assertEqual('stuv', zc['shelf']['name'])
        #
        book = self.fetch('/api/authorbook?author=2')
        meta = book['meta']
        self.assertEqual(1, meta['count'])
        zc = book['objects'][0]
        self.assertTrue('/api/authorbook/' in zc['resourceUri'])
        self.assertEqual('The Sun Also Rises', zc['book']['title'])
        self.assertEqual('efgh', zc['author']['name'])
        self.assertEqual('wxyz', zc['shelf']['name'])
