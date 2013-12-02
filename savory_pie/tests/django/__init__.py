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
    }
}
