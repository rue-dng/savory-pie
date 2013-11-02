===========================
Example apps for Savory Pie
===========================

In the last 2 or 3 weeks, I have been doing a lot of work with save conflicts, colliding
database transactions, etc. The client side of this stuff mostly lives in our savoryService.js
file. I would like to move that stuff into the Savory Pie repository, but of course I
need to remove dependencies upon (1) AngularJSj, and (2) our approach to data services,
which a user might not wish to use. There will be at minimum a need for a dependency upon
jQuery and/or UnderscoreJS. I think of jQuery as one of those things that has been around
forever that is in nearly-universal use. The same can't be said for AngularJS, and I don't
know about UnderscoreJS.

That's probably a good Nick question. What I'm trying to achieve is to get the stuff I'm
currently doing in savoryService.js, but in a way that doesn't turn off any future SPie
users, like the complaint would be "I would love to use Savory Pie but it can't be used
without XYZ JavaScript library, which deeply offends or frightens me".

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

Haystack, Whoosh/ElasticSearch, indexing, templates. Deployment stuff.

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
