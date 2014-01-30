Will's Savory Pie Brain Dump
============================

Savory Pie was originally intended to support a wider range of platforms than just Django,
but of course it is the only area that has gotten any significant work. So my comments here
will probably be entirely Django-specific. Wikipedia's article on
[REST](http://en.wikipedia.org/wiki/Representational_state_transfer#Applied_to_Web_Services)
tells what we want to present to a client, and Savory Pie is a wrapper around Django's ORM
to try to conform to that.

Here is a
[link](https://github.com/RueLaLa/savory-pie/blob/wware-spie-brain-dump/NOTES.md)
to this document.

**NOTE**: This document contains some Rue-specific language that should be purged, if we
want to include it in an open-source release some day.

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
base class. Some field methods deserve special attention.

* The
  [handle_outgoing](https://github.com/RueLaLa/savory-pie/blob/ac61c18f51f88bce163ca45612f4ef38df93e26b/savory_pie/fields.py#L165)
  method is used for GET operations. Data retrieved from the database
  is converted to JSON which goes out to the client. There is a context containing a
  formatter (used in
  [to_api_value](https://github.com/RueLaLa/savory-pie/blob/ac61c18f51f88bce163ca45612f4ef38df93e26b/savory_pie/fields.py#L174)
  and
  [\_compute\_property](https://github.com/RueLaLa/savory-pie/blob/ac61c18f51f88bce163ca45612f4ef38df93e26b/savory_pie/fields.py#L116))
  which allows users to customize both the field names (Django's underscored field
  names appear in the JSON as camelCase) and the appearance of values. In addition
  to camelCase,
  [our formatter](https://github.com/RueLaLa/savory-pie/blob/ac61c18f51f88bce163ca45612f4ef38df93e26b/savory_pie/formatters.py)
  also does a lot of formatting with dates and datetimes.

* The
  [handle_incoming](https://github.com/RueLaLa/savory-pie/blob/ac61c18f51f88bce163ca45612f4ef38df93e26b/savory_pie/fields.py#L152)
  method handles PUT and POST operations. The context's formatter has a role here that is
  similar but reversed.

* If you go into rue-storemanager and type `git grep -C 15 'def handle_incoming'` or
  `git grep -C 15 'def handle_outgoing'`, you'll see several places where we have
  defined customized fields with special operations on these methods. This is a handy
  way to handle "out of band" needs, such as communication with the OMS broker.

* The
  [save](https://github.com/RueLaLa/savory-pie/blob/ac61c18f51f88bce163ca45612f4ef38df93e26b/savory_pie/django/fields.py#L103)
  method is where Mike implemented his dirty bit stuff, where we don't bother to save
  something if we haven't made any changes in it. Mike can provide more information
  about this.

In Django language, the word
["related"](https://docs.djangoproject.com/en/dev/ref/models/relations/)
means that model Leaf has a foreign key to model Tree,
so that when you refer to `someSpecificTree.leaves`, you get a list of the leaves on that
specific tree. That's a one-to-many relationship, there are also
[many-to-many](https://docs.djangoproject.com/en/dev/topics/db/examples/many_to_many/)
relationships.

Other fields, to be documented as I gradually overcome my laziness:
* [AttributeFieldWithModel](https://github.com/RueLaLa/savory-pie/blob/ac61c18f51f88bce163ca45612f4ef38df93e26b/savory_pie/django/fields.py#L124-L154)
  handles cases where we refer to a submodel's attribute field through the containing
  object. For instance if a FooContext has a foreign key to a Foo, and the Foo has a
  Bar Attribute, you'd see something like
  `AttributeFieldWithModel('foo.bar', type=int, model=Foo)`
  which would appear in the JSON as simply `bar`. A real-world usage of this appears
  [here](https://github.com/RueLaLa/rue-storemanager/blob/82f963a6e8aa27df463c7ff585fc0c0de4e97921/rue/storemanager/api2/product.py#L401).
* [URIResourceField](https://github.com/RueLaLa/savory-pie/blob/ac61c18f51f88bce163ca45612f4ef38df93e26b/savory_pie/django/fields.py#L221-L241),
  a foreign key to another model in the form of a URI, several examples
  appear in [rue/storemanager/api2/context.py](https://github.com/RueLaLa/rue-storemanager/blob/82f963a6e8aa27df463c7ff585fc0c0de4e97921/rue/storemanager/api2/context.py).
  We often use this to avoid gigantic JSON objects coming back to the browser, as would result
  if we got a long list of products and each had a long list of SKUs, and each SKU carries a
  boatload of JSON.
* [URIListResourceField](https://github.com/RueLaLa/savory-pie/blob/ac61c18f51f88bce163ca45612f4ef38df93e26b/savory_pie/django/fields.py#L256-L266),
  a list of related objects (see above) in the form of URIs. I believe
  this is simply a plural form of URIResourceField.
* [SubModelResourceField](https://github.com/RueLaLa/savory-pie/blob/ac61c18f51f88bce163ca45612f4ef38df93e26b/savory_pie/django/fields.py#L277-L295),
  another list of related objects, but this time we are including
  the JSON for each one as part of a giant JSON array. Be careful of exponential JSON
  explosion here.
* [OneToOneField](https://github.com/RueLaLa/savory-pie/blob/ac61c18f51f88bce163ca45612f4ef38df93e26b/savory_pie/django/fields.py#L387-L395),
  used for Django
  [one-to-one](https://docs.djangoproject.com/en/dev/topics/db/examples/one_to_one/)
  relationships.
* [RelatedManagerField](https://github.com/RueLaLa/savory-pie/blob/ac61c18f51f88bce163ca45612f4ef38df93e26b/savory_pie/django/fields.py#L415-L422),
  I don't remember how this works, but it is used in a few places in
  [rue/storemanager/api2/context.py](https://github.com/RueLaLa/rue-storemanager/blob/82f963a6e8aa27df463c7ff585fc0c0de4e97921/rue/storemanager/api2/context.py).
* [ReverseField](https://github.com/RueLaLa/savory-pie/blob/ac61c18f51f88bce163ca45612f4ef38df93e26b/savory_pie/django/fields.py#L456-L467),
  handles a one-to-one relationship where the other object has a foreign key back to this
  object. This field is ignored in PUT or POST operations (`handle_incoming` is a no-op).
* ReverseRelatedManagerField, this is one I invented, and it turned out to be a bad idea.
  It isn't used anywhere and it shouldn't be used anywhere. Feel free to remove it.
* [AggregateField](https://github.com/RueLaLa/savory-pie/blob/ac61c18f51f88bce163ca45612f4ef38df93e26b/savory_pie/django/fields.py#L519-L534),
  deals with objects in aggregations, which is as murky to me as it is to you. Its only
  usage in our code is as the base class for RelatedCountField. `handle_incoming` is a no-op.
* [RelatedCountField](https://github.com/RueLaLa/savory-pie/blob/ac61c18f51f88bce163ca45612f4ef38df93e26b/savory_pie/django/fields.py#L594-L605),
  given a bunch of related objects pointing back to this object, it tells you how
  many of them exist. `handle_incoming` is a no-op.

Filters
-------

* [StandardFilter](https://github.com/RueLaLa/savory-pie/blob/09394269e197a42e6a3e9e2a48fcd0aa42c2768c/savory_pie/django/filters.py#L5-45)
* [ParameterizedFilter](https://github.com/RueLaLa/savory-pie/blob/09394269e197a42e6a3e9e2a48fcd0aa42c2768c/savory_pie/django/filters.py#L145-L150)
* [HaystackFilter](https://github.com/RueLaLa/savory-pie/blob/2712bd8e4cc575ff808631c3e9c3bcfa00711829/savory_pie/django/haystack_filter.py#L6-L11)

Filters are only useful in GET operations. The flow is that
[_process_get](https://github.com/RueLaLa/savory-pie/blob/2f6b123ce0a9f6236cc53222b6e133f1d0793770/savory_pie/django/views.py#L110-L115)
calls
[QuerySetResource.get](https://github.com/RueLaLa/savory-pie/blob/2f6b123ce0a9f6236cc53222b6e133f1d0793770/savory_pie/django/resources.py#L97)
which calls
[QuerySetResource.filter_queryset](https://github.com/RueLaLa/savory-pie/blob/2f6b123ce0a9f6236cc53222b6e133f1d0793770/savory_pie/django/resources.py#L55)
which calls the `filter` method on each filter in sequence. That `filter` method only
takes action if the filter is applicable, i.e. its keyword appears in the request's
[query string](http://en.wikipedia.org/wiki/Query_string).

Generally, filters have the following methods.
* The [constructor](https://github.com/RueLaLa/savory-pie/blob/2f6b123ce0a9f6236cc53222b6e133f1d0793770/savory_pie/django/filters.py#L47-L57)
  assigns the filter a name, gets criteria for filtering, and optionally gets a "order_by"
  argument to control the order in which results are given.
* The [is_applicable](https://github.com/RueLaLa/savory-pie/blob/2f6b123ce0a9f6236cc53222b6e133f1d0793770/savory_pie/django/filters.py#L83-L89)
  method determines whether this filter should be applied for a given GET request.
* The [apply](https://github.com/RueLaLa/savory-pie/blob/2f6b123ce0a9f6236cc53222b6e133f1d0793770/savory_pie/django/filters.py#L110-L113)
  method actually does the filtering operation on the queryset, calling the
  [build_queryset](https://github.com/RueLaLa/savory-pie/blob/2f6b123ce0a9f6236cc53222b6e133f1d0793770/savory_pie/django/filters.py#L96)
  method.
* The [filter](https://github.com/RueLaLa/savory-pie/blob/2f6b123ce0a9f6236cc53222b6e133f1d0793770/savory_pie/django/filters.py#L127-L131)
  method is a convenient wrapper for the `is_applicable` and `apply` methods. Also, for
  custom filters such as appear in
  [rue/storemanager/filters.py](https://github.com/RueLaLa/rue-storemanager/blob/82f963a6e8aa27df463c7ff585fc0c0de4e97921/rue/storemanager/filters.py),
  it's a handy place to override the filtering behavior.

Filters build collections of
[Q objects](https://docs.djangoproject.com/en/dev/topics/db/queries/#complex-lookups-with-q-objects)
that are used to perform
[lazy queries](https://docs.djangoproject.com/en/dev/topics/db/queries/#querysets-are-lazy).
You generally end up with a convoluted (but very efficient) SQL query
that brings back only the results you want. Query results are only actually
[evaluated at specific times](https://docs.djangoproject.com/en/dev/ref/models/querysets/#when-querysets-are-evaluated).

It's useful to look for examples of how filters are used, for example in
[src/rue-storemanager/rue/storemanager/filters.py](https://github.com/RueLaLa/rue-storemanager/blob/82f963a6e8aa27df463c7ff585fc0c0de4e97921/rue/storemanager/filters.py).

Validators
----------

Here are the fundamental pieces of the validator stuff.
* [validate (function)](https://github.com/RueLaLa/savory-pie/blob/02146cc1c70b4ca7aac5fa1d08228aab69f4b032/savory_pie/django/validators.py#L13-L38)
* [BaseValidator](https://github.com/RueLaLa/savory-pie/blob/02146cc1c70b4ca7aac5fa1d08228aab69f4b032/savory_pie/django/validators.py#L86-L159)
* [ResourceValidator](https://github.com/RueLaLa/savory-pie/blob/02146cc1c70b4ca7aac5fa1d08228aab69f4b032/savory_pie/django/validators.py#L230-L236)
* [FieldValidator](https://github.com/RueLaLa/savory-pie/blob/02146cc1c70b4ca7aac5fa1d08228aab69f4b032/savory_pie/django/validators.py#L498-L503)

Additionally,
[savory_pie/django/validators.py](https://github.com/RueLaLa/savory-pie/blob/02146cc1c70b4ca7aac5fa1d08228aab69f4b032/savory_pie/django/validators.py)
contains a lot of validators for specific purposes, and when you feel comfortable with the
overview of validators, those should be pretty easy to understand.

Validators are applied when we
[PUT](https://github.com/RueLaLa/savory-pie/blob/2f6b123ce0a9f6236cc53222b6e133f1d0793770/savory_pie/django/resources.py#L352)
a resource. The `validate` function has some logic for traversing the fields of a resource.
Validation is performed on a `source_dict` which wants to be PUT to a resource, and the
validation process is supposed to prevent that if the data is unsuitable. For example:

    class ValidationTestResource(resources.ModelResource):
        parent_resource_path = 'users'
        model_class = User

        validators = [
            DatetimeFieldSequenceValidator('start_date', 'end_date')
        ]

        fields = [
            fields.AttributeField(attribute='name', type=str,
                validator=StringFieldExactMatchValidator('Bob')),
            fields.AttributeField(attribute='age', type=int,
                validator=(IntFieldMinValidator(21, 'too young to drink'),
                           IntFieldPrimeValidator(100))),
                # A field can take either a single validator,
                # or a list or tuple of multiple validators.
            fields.AttributeField(attribute='before', type=datetime),
            fields.AttributeField(attribute='after', type=datetime),
            fields.AttributeField(attribute='systolic_bp', type=int,
                validator=IntFieldRangeValidator(100, 120,
                    'blood pressure out of range')),
        ]


When you apply *BaseValidator.validate* to an instance of ValidationTestResource,
it will check to see if all the criteria are satisfied, and will return a dict giving
all violations as key-value pairs, where the keys are dotted Python names for the
model or field in question, and the values are lists of error messages. So if several
criteria fail to be met, you might see something like this:

    {
        'savory_pie.tests.django.test_validators.ValidationTestResource':
            ['Datetimes are not in expected sequence.'],
        'savory_pie.tests.django.test_validators.ValidationTestResource.age':
            ['too young to drink',
             'This should be a prime number.'],
        'savory_pie.tests.django.test_validators.ValidationTestResource.name':
            ['This should exactly match the expected value.'],
        'savory_pie.tests.django.test_validators.ValidationTestResource.systolic_bp':
            ['blood pressure out of range']
    }

You can write your own validators, like *IntFieldPrimeValidator* above:

    class IntFieldPrimeValidator(FieldValidator):

        error_message = 'This should be a prime number.'

        def __init__(self, maxprime):
            self._primes = _primes = [2, 3, 5, 7]
            def test_prime(x, _primes=_primes):
                for p in _primes:
                    if p * p > x:
                        return True
                    if (x %% p) == 0:
                        return False
            for x in range(11, maxprime + 1, 2):
                if test_prime(x):
                    _primes.append(x)

        def check_value(self, value):
            return value in self._primes

As a general rule, a validator has a *find_errors* method which makes calls to the
*check_value* method, and if errors are found, they are stored in a dict, keyed by
the dotted name of the non-compliant model or field.


Merging my changes with yours
-----------------------------

This is a topic on which Ari is also knowledgeable. When you GET a resource or a list of
resources, the JSON includes an MD5 hash. If you later repeat the GET and the hash has
changed, that means the data has changed. When you PUT some data to a resource, you can
optionally specify an `If-Match` header with the hash value that you expect. If the
hash value has changed (because somebody else did a PUT while you were busy) then you'll
get a HTTP 412 status code, and no PUT will occur. This is done inside a database
transaction, and any changes are rolled back in the event of a 412 status.

Here's the scenario. You've pulled up a page with a form, and you change several fields
on the form. Unknown to you, somebody else is also making changes to the same form, and
they hit 'Save' while you're still working. When you hit 'Save', the first attempt to PUT
the data will give a 412 status. At this point you want to do
[an elaborate dance in the browser](https://github.com/RueLaLa/rue-storemanager/blob/f3bc527aec3ad79121d5d6b79d8d0828128504f3/rue/static/app/savoryService.js#L170-194)
where you decide whether the changes made by the other person are safely mergeable with
your changes. Usually this can be done invisibly behind the scenes and the user doesn't
even need to know that any arm-wrestling was taking place.

Merging changes gets a little tricky if the PUT is of a resource whose JSON includes JSON
for sub-resources. Currently we do this in the
[boutique.js](https://github.com/RueLaLa/rue-storemanager/blob/f3bc527aec3ad79121d5d6b79d8d0828128504f3/rue/static/app/data_services/boutique.js#L292-371)
and
[product.js](https://github.com/RueLaLa/rue-storemanager/blob/04c2b4dc8aed94ce32d65349ae8dfc26f4394f3d/rue/static/app/data_services/product.js#L525-549)
data services.

One more tricky thing involves an HTTP status of 409, which is the case where the server
is in the middle of a database transaction when another request comes in, and what the
client should do in this case is
[back off and re-try](https://github.com/RueLaLa/rue-storemanager/blob/516e597b97d152f56ba12a6e3a5b60a61b9e3e3c/rue/static/app/savoryService.js#L211-235).

These two JavaScript tricks should ideally be moved into the Savory Pie repository, because
if we ever really open-source it as we talked about doing, anybody using it will want those.
Obviously anything Rue-specific would need to be purged, and an overloading class in the
Storemanager repository would reinstate it.