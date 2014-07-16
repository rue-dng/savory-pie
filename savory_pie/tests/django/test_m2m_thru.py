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

_groups = []


class Group(mock_orm.Model):
    name = Mock(name='group.name')
    pk = Mock(name='group.pk')


class GroupResource(resources.ModelResource):
    parent_resource_path = 'groups'
    model_class = Group

    fields = [
        fields.AttributeField('name', type=str),
    ]


class GroupQuerySetResource(resources.QuerySetResource):
    resource_path = 'group'
    resource_class = GroupResource

createGroup = createCreator(Group, _groups)

######################

_people = []


class Person(mock_orm.Model):
    name = Mock(name='person.name')
    groups = Mock(name='person.groups')
    pk = Mock(name='person.pk')

Person.groups.all.return_value = _groups
del Person.groups.add      # this is a "through" relationship
del Person.groups.remove
Person.groups.source_field_name = 'person'
Person.groups.target_field_name = 'group'


class PersonResource(resources.ModelResource):
    parent_resource_path = 'person'
    model_class = Person

    fields = [
        fields.AttributeField('name', type=str),
        fields.RelatedManagerField('groups', GroupResource),
    ]


class PersonQuerySetResource(resources.QuerySetResource):
    resource_path = 'person'
    resource_class = PersonResource

createPerson = createCreator(Person, _people)

######################

_memberships = []


class Membership(mock_orm.Model):
    group = Mock(django.db.models.fields.related.ReverseSingleRelatedObjectDescriptor(Mock()))
    person = Mock(django.db.models.fields.related.ReverseSingleRelatedObjectDescriptor(Mock()))
    pk = Mock()
    objects = Mock()


class MembershipResource(resources.ModelResource):
    parent_resource_path = 'membership'
    model_class = Membership

    fields = [
        fields.RelatedManagerField('group', GroupResource),
        fields.RelatedManagerField('person', PersonResource),
    ]

Person.groups.through = Membership


class MembershipQuerySetResource(resources.QuerySetResource):
    resource_path = 'membership'
    resource_class = MembershipResource

createMembership = createCreator(Membership, _memberships)

Membership.objects.create = createMembership

##########


class ManyToManyThroughTest(unittest.TestCase):

    def setUp(self):
        createGroup(name='Rotary Club', pk=1)
        createGroup(name='Boston Python Meetup', pk=2)
        createPerson(name='Alice', pk=3)
        createPerson(name='Bob', pk=4)
        # Alice is a member of the Rotary Club
        createMembership(group=_groups[0], person=_people[0], pk=5)
        # Bob is a member of the Boston Python Meetup
        createMembership(group=_groups[1], person=_people[1], pk=6)

    def tearDown(self):
        global _groups, _people, _memberships
        del _groups[:]
        del _people[:]
        del _memberships[:]

    def test_check_add(self):
        related = PersonResource.fields[1]
        # When the add method is missing, we know it's a "through" M2M relationship.
        self.assertFalse(hasattr(related, 'add'))

    @unittest.skipIf(
        True,
        """
        This test is broken, but somewhat replaced by RelatedManagerFieldTest.test_incoming_m2m_add
        and RelatedManagerFieldTest.test_incoming_m2m_delete'
        """
    )
    def test_m2m_through(self):
        ctx = mock_context()

        def resolve(*args):
            prefix = 'http://localhost:8000/api/'
            self.assertTrue(args[0].startswith(prefix))
            arg = args[0][len(prefix):]
            if arg.startswith('group/'):
                n = int(arg[6:]) - 1
                assert n < len(_groups), n
                return GroupResource(_groups[n])
            elif arg.startswith('person/'):
                n = int(arg[7:]) - 1
                assert n < len(_people), n
                return PersonResource(_people[n])
            else:
                self.fail(arg)

        ctx.resolve_resource_uri = resolve
        source_dict = {
            'groups': [{'resourceUri': 'http://localhost:8000/api/group/1', 'name': 'Boy Scouts'}],
            'resourceUri': 'http://localhost:8000/api/person/1',
            'name': 'Charlie'
        }
        resource = PersonResource(_people[0])
        resource.put(ctx, source_dict)
        self.assertEqual('Boy Scouts', _groups[0].name)
        self.assertEqual(3, len(_memberships))
        resource = GroupResource(_groups[0])
        self.assertEqual({'resourceUri': 'uri://groups/1',
                          'name': 'Boy Scouts',
                          '$hash': 'a35a8e769bb1583a840525d1e8fd6b3d02658b04'},
                         resource.get(ctx, {'resourceUri': 'http://localhost:8000/api/group/1'}))
