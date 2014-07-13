import os

# Only here so django can be imported
USE_TZ = True
SECRET_KEY = 'ecret-say_ey-kay'

PROJECT_ROOT = os.path.join(os.path.dirname(__file__))
TEMPLATE_DIRS = (os.path.join(PROJECT_ROOT, 'templates'),)

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
    },
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

INSTALLED_APPS = [
    'haystack',
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'savory_pie': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'filters': []
        }
    }
}
