#####################################
#                                   #
#         Savory Pie stuff          #
#                                   #
#####################################

import pprint

from django.contrib import admin
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from savory_pie.resources import APIResource
from savory_pie.django import fields, resources, filters
from savory_pie.formatters import JSONFormatter

from myproject.models import Author, Book, Shelf, AuthorBook


class PrettyJSONFormatter(JSONFormatter):
    def write_to(self, body_dict, response):
        pprint.pprint(body_dict, stream=response)


class AuthorResource(resources.ModelResource):
    parent_resource_path = 'author'
    model_class = Author

    fields = [
        fields.AttributeField('name', type=str),
    ]


class BookResource(resources.ModelResource):
    parent_resource_path = 'book'
    model_class = Book

    fields = [
        fields.AttributeField('title', type=str),
        fields.RelatedManagerField('authors', AuthorResource),
    ]


class ShelfResource(resources.ModelResource):
    parent_resource_path = 'shelf'
    model_class = Shelf

    fields = [
        fields.AttributeField('name', type=str),
    ]


class AuthorBookResource(resources.ModelResource):
    parent_resource_path = 'authorbook'
    model_class = AuthorBook

    fields = [
        fields.SubModelResourceField('author', AuthorResource),
        fields.SubModelResourceField('book', BookResource),
        fields.SubModelResourceField('shelf', ShelfResource)
    ]


class AuthorQuerySetResource(resources.QuerySetResource):
    resource_path = 'author'
    resource_class = AuthorResource
    page_size = 200


class BookQuerySetResource(resources.QuerySetResource):
    resource_path = 'book'
    resource_class = BookResource
    page_size = 200


class ShelfQuerySetResource(resources.QuerySetResource):
    resource_path = 'shelf'
    resource_class = ShelfResource
    page_size = 200


class AuthorBookQuerySetResource(resources.QuerySetResource):
    resource_path = 'authorbook'
    resource_class = AuthorBookResource
    filters = [
        filters.StandardFilter('authorOne', {'author__id': 1}),
        filters.ParameterizedFilter('author', 'author__id'),
    ]

root_resource = APIResource()
root_resource.register_class(AuthorQuerySetResource)
root_resource.register_class(BookQuerySetResource)
root_resource.register_class(AuthorBookQuerySetResource)
