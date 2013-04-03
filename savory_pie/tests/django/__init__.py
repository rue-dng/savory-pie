from datetime import datetime
from savory_pie import formatters
import pytz

json_formatter = formatters.JSONFormatter()
date_str = json_formatter.to_api_value(datetime, datetime.now(pytz.UTC))

#TODO add filtering and sort order
user_resource_schema = {
    'allowedDetailHttpMethods': ['put', 'delete', 'get'],
    'allowedListHttpMethods': ['put', 'delete', 'get'],
    'defaultFormat': 'application/json',
    'defaultLimit': 0,
    'filtering': {},
    'ordering': [],
    'resourceUri': 'uri://user/schema/',
    'fields': {
        'username': {
            'nullable': False,
            'default': u'',
            'readonly': False,
            'helpText': u'Required. 30 characters or fewer. Letters, numbers and @/./+/-/_ characters',
            'blank': False,
            'unique': True,
            'type': 'str',
            'validators': []
        },
        'lastLogin': {
            'nullable': False,
            'default': date_str,
            'readonly': False,
            'helpText': u'',
            'blank': False,
            'unique': False,
            'type': 'datetime',
            'validators': []
        },
        'firstName': {
            'nullable': False,
            'default': u'',
            'readonly': False,
            'helpText': u'',
            'blank': True,
            'unique': False,
            'type': 'str',
            'validators': []
        },
        'userPermissions': {
            'nullable': False,
            'default': u'',
            'relatedType': 'to_many',
            'readonly': False,
            'helpText': u'Specific permissions for this user. Hold down "Control", or "Command" on a Mac, to select more than one.',
            'blank': True,
            'unique': False,
            'type': 'related',
            'validators': []
        },
        'lastName': {
            'nullable': False,
            'default': u'',
            'readonly': False,
            'helpText': u'',
            'blank': True,
            'unique': False,
            'type': 'str',
            'validators': []
        },
        'isSuperuser': {
            'nullable': False,
            'default': False,
            'readonly': False,
            'helpText': u'Designates that this user has all permissions without explicitly assigning them.',
            'blank': True,
            'unique': False,
            'type': 'bool',
            'validators': []
        },
        'dateJoined': {
            'nullable': False,
            'default': date_str,
            'readonly': False,
            'helpText': u'',
            'blank': False,
            'unique': False,
            'type': 'datetime',
            'validators': []
        },
        'isStaff': {
            'nullable': False,
            'default': False,
            'readonly': False,
            'helpText': u'Designates whether the user can log into this admin site.',
            'blank': True,
            'unique': False,
            'type': 'bool',
            'validators': []
        },
        'groups': {
            'nullable': False,
            'default': u'',
            'relatedType': 'to_many',
            'readonly': False,
            'helpText': u'The groups this user belongs to. A user will get all permissions granted to each of his/her group. Hold down "Control", or "Command" on a Mac, to select more than one.',
            'blank': True,
            'unique': False,
            'type': 'related',
            'validators': []
        },
        'pk': {
            'nullable': False,
            'default': None,
            'readonly': False,
            'helpText': u'',
            'blank': True,
            'unique': True,
            'type': 'int',
            'validators': []
        },
        'password': {
            'nullable': False,
            'default': u'',
            'readonly': False,
            'helpText': u'',
            'blank': False,
            'unique': False,
            'type': 'str',
            'validators': []
        },
        'email': {
            'nullable': False,
            'default': u'',
            'readonly': False,
            'helpText': u'',
            'blank': True,
            'unique': False,
            'type': 'str',
            'validators': []
        },
        'isActive': {
            'nullable': False,
            'default': True,
            'readonly': False,
            'helpText': u'Designates whether this user should be treated as active. Unselect this instead of deleting accounts.',
            'blank': True,
            'unique': False,
            'type': 'bool',
            'validators': []
        }
    }
}
