from django.conf.urls import patterns, include, url
from django.contrib import admin

from myproject.models import Author, Book, AuthorBook
from myproject.api.models import root_resource as api_root_resource

import os, sys
sys.path.append(os.path.realpath("../savory-pie"))

from savory_pie.django.views import api_view

admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'myproject.views.home', name='home'),
    url(r'^$', 'myproject.views.home', name='home'),
    # url(r'^myproject/', include('myproject.foo.urls')),

    url(r'^api/(.*)$', api_view(api_root_resource)),

    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
