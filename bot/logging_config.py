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
            'maxBytes': 2048,
            'backupCount': 3
        }
    },
    'loggers': {
        'bot': {
            'level': 'INFO',
            'handlers': ['console', 'file'],
        },
        'bot.handlers': {
            'level': 'INFO',
            'propagate': True,
        },
    }
}
