"""
Test settings for Django project
Optimized for fast testing with minimal external dependencies
"""

from .base import *
import tempfile
import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Test database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # Use in-memory database for faster tests
    }
}

# Disable migrations for faster tests
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Cache configuration for tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'test-cache',
    }
}

# Email backend for tests
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Static files for tests
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(tempfile.gettempdir(), 'static_test')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(tempfile.gettempdir(), 'media_test')

# Password validation (simplified for tests)
AUTH_PASSWORD_VALIDATORS = []

# Logging configuration for tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

# Test-specific settings
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# Disable CSRF for API tests
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# Disable external services for tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Test-specific apps (if any)
# INSTALLED_APPS += []

# Simplified middleware for tests
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

# Time zone for tests
USE_TZ = True

# Internationalization for tests
LANGUAGE_CODE = 'en-us'
USE_I18N = True
USE_L10N = True