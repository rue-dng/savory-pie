Will's Savory Pie Brain Dump
============================

Savory Pie was originally intended to support a wider range of platforms than just Django,
but of course it is the only area that has gotten any significant work. So my comments here
will probably be entirely Django-specific. Wikipedia's article on
[REST](http://en.wikipedia.org/wiki/Representational_state_transfer#Applied_to_Web_Services)
tells what we want to present to a client, and Savory Pie is a wrapper around Django's ORM
to try to conform to that.

Resources
---------

With very few exceptions, we've mapped REST resources onto Django models. Django specifies a
thing called a [QuerySet](https://docs.djangoproject.com/en/dev/ref/models/querysets/) for
reading and modifying objects or collections of objects. This maps onto our
[QuerySetResource](https://github.com/RueLaLa/savory-pie/blob/ac61c18f51f88bce163ca45612f4ef38df93e26b/savory_pie/django/resources.py#L17-36), which
handles GET and POST. Generally you can think of QSR as a model for a class or collection, not
an individual instance.

Individual instances are modeled by the
[ModelResource](https://github.com/RueLaLa/savory-pie/blob/ac61c18f51f88bce163ca45612f4ef38df93e26b/savory_pie/django/resources.py#L187-201),
which handles PUT and DELETE and single-object GET.

I should mention some divergences from these patterns.
[ATSResource](https://github.com/RueLaLa/rue-storemanager/blob/988f2bfc365e93ad6ef257dedc5c2d7d12573ddd/rue/storemanager/api2/ats.py#L16-20)
implements GET and PUT directly for an individual ATS resource, without going through a Django
model. Instead it goes through the inventory server on GET, and the OMS broker on PUT. (I think
the inventory server turns out to be effectively a proxy for the OMS broker. Exercise left to
the reader.)

I thought I remembered another example, maybe it will come back to me.

The point is, as long as you're following the APIs for ModelResource and QuerySetResource, you
don't necessarily need to connect to Django models. If a resource GET did a direct read from a
thermometer, it would still work as an API but would require no connection to Django's database.

Fields
------

Django models have fields, and we represent them with Savory Pie fields which allow you to
read and write the field values with JSON, in GET, PUT, and POST operations.

The simplest field is
[savory_pie.django.AttributeField](https://github.com/RueLaLa/savory-pie/blob/ac61c18f51f88bce163ca45612f4ef38df93e26b/savory_pie/django/fields.py#L67-87).
This is used when a model's field is a simple value like an int, a float, or a string.
A lot of the machinery for AttributeField comes from the
[savory_pie.AttributeField](https://github.com/RueLaLa/savory-pie/blob/ac61c18f51f88bce163ca45612f4ef38df93e26b/savory_pie/fields.py#L61-98)
base class.

Two methods of fields deserve special attention.

* The
  [handle_outgoing](https://github.com/RueLaLa/savory-pie/blob/ac61c18f51f88bce163ca45612f4ef38df93e26b/savory_pie/fields.py#L165)
  method is used for GET operations. Data retrieved from the database
  is converted to JSON which goes out to the client. There is a context containing a
  formatter (used in
  [to_api_value](https://github.com/RueLaLa/savory-pie/blob/ac61c18f51f88bce163ca45612f4ef38df93e26b/savory_pie/fields.py#L174)
  and
  [_compute_property](https://github.com/RueLaLa/savory-pie/blob/ac61c18f51f88bce163ca45612f4ef38df93e26b/savory_pie/fields.py#L116))
  which allows users to customize both the field names (Django's underscored field
  names appear in the JSON as camelCase) and the appearance of values. In addition
  to camelCase,
  [our formatter](https://github.com/RueLaLa/savory-pie/blob/ac61c18f51f88bce163ca45612f4ef38df93e26b/savory_pie/formatters.py)
  also does a lot of formatting with dates and datetimes.

* The
  [handle_incoming](https://github.com/RueLaLa/savory-pie/blob/ac61c18f51f88bce163ca45612f4ef38df93e26b/savory_pie/fields.py#L152)
  handles PUT and POST operations. The context's formatter has a role here that is
  similar but reversed.

If you go into rue-storemanager and type `git grep -C 15 'def handle_incoming'` or
`git grep -C 15 'def handle_outgoing'`, you'll see several places where we have
defined customized fields with special operations on these methods. This is a handy
way to handle "out of band" needs, such as communication with the OMS broker.










