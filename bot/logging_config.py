LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'basic': {
            'format': '%(levelname)s %(asctime)s - %(message)s',
            'datefmt': '%d-%b-%y %H:%M:%S'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'basic',
            'level': 'INFO',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'basic',
            'filename': 'app.log',
            'maxBytes': 100 * 2 ** 20,
            'backupCount': 10
        }
    },
    'loggers': {
        '': {
            'level': 'INFO',
            'propagate': True,
            'handlers': ['console', 'file'],
        },
        'bot': {
            'level': 'INFO',
            'propagate': True
        },
        'bot.handlers': {
            'level': 'INFO',
            'propagate': True,
        },
    }
}
