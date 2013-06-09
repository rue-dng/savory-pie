import unittest
from mock import Mock

import django.core.exceptions

from savory_pie.django import resources, fields
from savory_pie.tests.django import mock_orm
from savory_pie.tests.mock_context import mock_context


def createCreator(model_class, collection):
    def createObject(**kwargs):
        obj = model_class(**kwargs)
        collection.append(obj)
        return obj
    return createObject

####################

_zones = []


class Zone(mock_orm.Model):
    name = Mock(name='zone.name')
    pk = Mock(name='zone.pk')


class ZoneResource(resources.ModelResource):
    parent_resource_path = 'zones'
    model_class = Zone

    fields = [
        fields.AttributeField('name', type=str),
    ]


class ZoneQuerySetResource(resources.QuerySetResource):
    resource_path = 'zone'
    resource_class = ZoneResource

createZone = createCreator(Zone, _zones)

######################

_contents = []


class Content(mock_orm.Model):
    title = Mock(name='content.title')
    zones = Mock(name='content.zones')
    pk = Mock(name='content.pk')

Content.zones.all.return_value = _zones
del Content.zones.add      # this is a "through" relationship
del Content.zones.remove
Content.zones.source_field_name = 'content'
Content.zones.target_field_name = 'zone'


class ContentResource(resources.ModelResource):
    parent_resource_path = 'content'
    model_class = Content

    fields = [
        fields.AttributeField('title', type=str),
        fields.RelatedManagerField('zones', ZoneResource),
    ]


class ContentQuerySetResource(resources.QuerySetResource):
    resource_path = 'content'
    resource_class = ContentResource

createContent = createCreator(Content, _contents)

######################

_zonecontents = []


class ZoneContent(mock_orm.Model):
    zone = Mock(django.db.models.fields.related.ReverseSingleRelatedObjectDescriptor(Mock()))
    content = Mock(django.db.models.fields.related.ReverseSingleRelatedObjectDescriptor(Mock()))
    pk = Mock()
    objects = Mock()


class ZoneContentResource(resources.ModelResource):
    parent_resource_path = 'zonecontent'
    model_class = ZoneContent

    fields = [
        fields.RelatedManagerField('zone', ZoneResource),
        fields.RelatedManagerField('content', ContentResource),
    ]

Content.zones.through = ZoneContent


class ZoneContentQuerySetResource(resources.QuerySetResource):
    resource_path = 'zonecontent'
    resource_class = ZoneContentResource

createZoneContent = createCreator(ZoneContent, _zonecontents)

ZoneContent.objects.create = createZoneContent

##########


class ManyToManyThroughTest(unittest.TestCase):

    def setUp(self):
        createZone(name='abcd', pk=1)
        createZone(name='efgh', pk=2)
        createContent(title='A Tree Grows in Brooklyn', pk=3)
        createContent(title='The Sun Also Rises', pk=4)
        createZoneContent(zone=_zones[0], content=_contents[0], pk=5)
        createZoneContent(zone=_zones[1], content=_contents[1], pk=6)

    def tearDown(self):
        global _zones, _contents, _zonecontents
        del _zones[:]
        del _contents[:]
        del _zonecontents[:]

    def test_check_add(self):
        related = ContentResource.fields[1]
        # When the add method is missing, we know it's a "through" M2M relationship.
        self.assertFalse(hasattr(related, 'add'))

    def test_m2m_through(self):
        ctx = mock_context()

        def resolve(*args):
            prefix = 'http://localhost:8000/api/'
            self.assertTrue(args[0].startswith(prefix))
            arg = args[0][len(prefix):]
            if arg.startswith('zone/'):
                n = int(arg[5:]) - 1
                assert n < len(_zones), n
                return ZoneResource(_zones[n])
            elif arg.startswith('content/'):
                n = int(arg[8:]) - 1
                assert n < len(_contents), n
                return ContentResource(_contents[n])
            else:
                self.fail(arg)
        ctx.resolve_resource_uri = resolve
        source_dict = {
            'zones': [{'resourceUri': 'http://localhost:8000/api/zone/1', 'name': 'quux'}],
            'resourceUri': 'http://localhost:8000/api/content/1',
            'title': 'Harry Potter and the Endless Sequels'
        }
        resource = ContentResource(_contents[0])
        resource.put(ctx, source_dict)
        self.assertEqual('quux', _zones[0].name)
        self.assertEqual(3, len(_zonecontents))
        resource = ZoneResource(_zones[0])
        self.assertEqual({'resourceUri': 'uri://zones/1', 'name': 'quux'},
                         resource.get(ctx, {'resourceUri': 'http://localhost:8000/api/zone/1'}))
