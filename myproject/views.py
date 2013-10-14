import json

from django.contrib.auth.decorators import login_required
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.core import serializers
from savory_pie.resources import EmptyParams
from myproject.api.models import AuthorResource

from models import Author, Book, AuthorBook, Shelf

def home(request):
    return render_to_response('base.html', {
        'authors': [z.to_json() for z in Author.objects.all()],
        'books': [z.to_json() for z in Book.objects.all()],
        'shelfs': [z.to_json() for z in Shelf.objects.all()],
        'authorbooks': [z.to_json() for z in AuthorBook.objects.all()],
        })
