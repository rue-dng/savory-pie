# Only here so django can be imported
USE_TZ = True
SECRET_KEY = 'ecret-say_ey-kay'

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
        'console':{
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
