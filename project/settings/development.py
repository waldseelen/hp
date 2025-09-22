"""
Development settings for portfolio project
Enhanced with fix all.yml optimizations
"""

from .base import *
import os

# Development settings
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# ==========================================================================
# DEVELOPMENT ENVIRONMENT OPTIMIZATIONS (from fix all.yml)
# ==========================================================================

# Development server environment variables
os.environ.setdefault('DJANGO_DEBUG', 'True')
os.environ.setdefault('DJANGO_DEVELOPMENT_SERVER', 'True')

# Template optimization for development
TEMPLATES[0]['OPTIONS']['context_processors'].extend([
    'django.template.context_processors.debug',
])

# Enable template debugging
TEMPLATES[0]['OPTIONS']['debug'] = True

# Disable template caching for development
TEMPLATES[0]['OPTIONS']['loaders'] = [
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
]

# Database for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR.parent / 'static',
]

# Development email backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Development cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Development logging with enhanced error monitoring
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'verbose',
        },
        'template_errors': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'template_errors_dev.log',
            'level': 'ERROR',
            'formatter': 'verbose',
        },
        'server_management': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'server_management_dev.log',
            'level': 'INFO',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'main.template_errors': {
            'handlers': ['template_errors', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'main.server_management': {
            'handlers': ['server_management', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.template': {
            'handlers': ['template_errors', 'console'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}

# Development auto-detection
DEVELOPMENT_AUTO_DETECTION = {
    'DETECT_DJANGO_PROJECT': True,
    'FIND_MANAGE_PY': True,
    'DETECT_SETTINGS_MODULE': True,
}

# Development optimization settings
DEVELOPMENT_OPTIMIZATION = {
    'CACHE_TEMPLATES': False,  # Disable template caching
    'AUTO_RELOAD': True,       # Enable auto-reload
    'DEBUG_TOOLBAR': DEBUG,    # Enable debug toolbar in debug mode
}

# Development security settings
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Debug toolbar for development (commented out - install django-debug-toolbar if needed)
# if DEBUG:
#     INSTALLED_APPS += ['debug_toolbar']
#     MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
#     INTERNAL_IPS = ['127.0.0.1']