===========================
Example apps for Savory Pie
===========================

The apps
========

Each of the items below should be an app, differentiated by the first component of the
URL path. There should be a unifying app that helps a newbie navigate among them.

Basic example
-------------

Take a very simple Django app, like the polls-and-questions app in the official tutorial,
and provide a basic API for it. Give plenty of tests and explain everything. Provide some
client-side test scripts that do various CRUD operations from the command line.

Resource, QuerySetResource, AttributeField

QuerySet stuff
--------------

https://docs.djangoproject.com/en/dev/ref/models/querysets/

How QuerySetResource makes QuerySet methods available in the Savory Pie world.

Filtering
---------

StandardFilter, ParameterizedFilter, how to write your own filters, examples.

Haystack search
---------------

Haystack, Whoosh, indexing, templates. Deployment stuff?

All those crazy fields
----------------------

Fields defined in savory_pie.fields and savory_pie.django.fields. Explanations and examples
for each. Avoiding infinite regress in generating JSON. When to define multiple resources for
a Django model.

Many-to-many and through
------------------------

Example of those.

Prefetch_related and select_related
-----------------------------------

Database queries, DB performance, "only" and "exclude", performance advice, how to measure
performance, joins, normalization, pointers to educational stuff about DBs.

Other stuff to do
=================

A tool that generates a graphviz picture of an API. How to identify when there are evil
cycles in an API, and how to fix them.
