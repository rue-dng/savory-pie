import datetime
import unittest
import sys
import os
from django.db import models, utils
from savory_pie.django import fields, resources, filters
from haystack import site, indexes
from haystack import fields as hayfields

os.environ['DJANGO_SETTINGS_MODULE']='savory_pie.tests.django.dummy_settings'


class User(models.Model):
    name = models.CharField(max_length=20)
    age = models.IntegerField()
    when = models.DateTimeField()


class UserResource(resources.ModelResource):
    parent_resource_path = 'users'
    model_class = User

    fields = [
        fields.AttributeField(attribute='name', type=str),
        fields.AttributeField(attribute='age', type=int),
        fields.AttributeField(attribute='when', type=datetime.datetime),
    ]


class UserQuerySetResource(resources.ModelResource):
    resource_path = 'users'
    resource_class = UserResource

    filters = [
        filters.HaystackFilter('haystack'),
    ]


class UserIndex(indexes.SearchIndex):
    text = hayfields.CharField(document=True, use_template=True)
    name = hayfields.CharField(model_attr='name')
    age = hayfields.IntegerField(model_attr='age')
    when = hayfields.CharField(model_attr='when')

    def get_model(self):
        return User

    def index_queryset(self):
        return User.objects.all()


site.register(User, UserIndex)
