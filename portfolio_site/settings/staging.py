"""
Django settings for staging environment.

Staging environment mirrors production but with relaxed security
and additional debugging capabilities for testing.
"""

from .base import *
import os

# =============================================================================
# CORE SETTINGS
# =============================================================================

# Debug mode (enabled for easier troubleshooting)
DEBUG = config('DEBUG', default=True, cast=bool)

# Allowed hosts
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1,*.railway.app,*.vercel.app',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

# Use PostgreSQL for staging (same as production)
DATABASES = {
    'default': dj_database_url.parse(
        config('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# =============================================================================
# CACHE CONFIGURATION
# =============================================================================

# Redis cache for staging
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/1')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        },
        'KEY_PREFIX': 'staging',
        'TIMEOUT': 300,  # 5 minutes
    }
}

# Use cache for sessions
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# =============================================================================
# SECURITY SETTINGS (Relaxed for staging)
# =============================================================================

# HTTPS settings (relaxed for staging)
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SECURE_HSTS_SECONDS = 0  # Disabled for staging
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Cookie settings
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=False, cast=bool)

# Content Security Policy (relaxed)
CSP_DEFAULT_SRC = ("'self'", "'unsafe-inline'", "'unsafe-eval'")
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "'unsafe-eval'", 'https:')
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", 'https:')
CSP_IMG_SRC = ("'self'", 'data:', 'https:')
CSP_FONT_SRC = ("'self'", 'https:')

# =============================================================================
# EMAIL CONFIGURATION
# =============================================================================

# Console email backend for staging
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend'
)

# SMTP settings (if configured)
if EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
    EMAIL_HOST = config('EMAIL_HOST', default='')
    EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
    EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
    EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
    EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')

DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='staging@portfolio.local')
SERVER_EMAIL = config('SERVER_EMAIL', default='staging@portfolio.local')

# =============================================================================
# STATIC FILES & MEDIA
# =============================================================================

# Static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Static files storage
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'json': {
            'format': '{"level": "%(levelname)s", "time": "%(asctime)s", "module": "%(module)s", "message": "%(message)s"}',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'staging.log'),
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# =============================================================================
# DEVELOPMENT & DEBUGGING
# =============================================================================

# Enable Django Debug Toolbar in staging
if DEBUG:
    INSTALLED_APPS += [
        'debug_toolbar',
    ]

    MIDDLEWARE += [
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    ]

    # Debug toolbar settings
    INTERNAL_IPS = [
        '127.0.0.1',
        'localhost',
    ]

    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TEMPLATE_CONTEXT': True,
        'SHOW_TOOLBAR_CALLBACK': lambda request: True,
    }

# =============================================================================
# MONITORING & OBSERVABILITY
# =============================================================================

# Sentry configuration (optional for staging)
SENTRY_DSN = config('SENTRY_DSN', default='')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration

    sentry_logging = LoggingIntegration(
        level=logging.INFO,
        event_level=logging.ERROR,
    )

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(
                auto_enabling_integrations=False,
                transaction_style='url',
                middleware_spans=True,
                signals_spans=True,
            ),
            sentry_logging,
        ],
        traces_sample_rate=0.1,  # Lower sample rate for staging
        send_default_pii=False,
        environment='staging',
        release=config('GIT_SHA', default='unknown'),
    )

# =============================================================================
# CELERY CONFIGURATION (if used)
# =============================================================================

# Celery broker
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default=REDIS_URL)
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default=REDIS_URL)

# Celery settings
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True

# Task routing
CELERY_TASK_ROUTES = {
    'apps.main.tasks.*': {'queue': 'main'},
    'apps.contact.tasks.*': {'queue': 'contact'},
}

# =============================================================================
# PERFORMANCE SETTINGS
# =============================================================================

# Database connection pooling
DATABASES['default']['CONN_MAX_AGE'] = 600

# Cache timeout settings
CACHE_TTL = {
    'default': 300,  # 5 minutes
    'long': 3600,    # 1 hour
    'short': 60,     # 1 minute
}

# =============================================================================
# TESTING CONFIGURATION
# =============================================================================

# Test settings
if 'test' in sys.argv or 'pytest' in sys.modules:
    # Use in-memory database for tests
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }

    # Disable migrations during tests
    class DisableMigrations:
        def __contains__(self, item):
            return True

        def __getitem__(self, item):
            return None

    MIGRATION_MODULES = DisableMigrations()

    # Use dummy cache for tests
    CACHES['default'] = {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }

    # Disable logging during tests
    LOGGING_CONFIG = None

# =============================================================================
# ADMIN CONFIGURATION
# =============================================================================

# Admin site header
ADMIN_SITE_HEADER = "Portfolio Site Staging"
ADMIN_SITE_TITLE = "Portfolio Staging"
ADMIN_INDEX_TITLE = "Staging Administration"

# =============================================================================
# STAGING-SPECIFIC FEATURES
# =============================================================================

# Enable staging banner
STAGING_BANNER = True
STAGING_BANNER_MESSAGE = "🚧 STAGING ENVIRONMENT - This is not the live site"

# Mock external services for staging
MOCK_EXTERNAL_SERVICES = config('MOCK_EXTERNAL_SERVICES', default=True, cast=bool)

# Test data seeding
ENABLE_TEST_DATA = config('ENABLE_TEST_DATA', default=True, cast=bool)

# API rate limiting (relaxed for staging)
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '1000/hour',
    'user': '2000/hour',
    'login': '50/hour',
}

# =============================================================================
# ENVIRONMENT VALIDATION
# =============================================================================

# Ensure staging environment is properly configured
REQUIRED_STAGING_SETTINGS = [
    'DATABASE_URL',
    'SECRET_KEY',
]

for setting in REQUIRED_STAGING_SETTINGS:
    if not config(setting, default=None):
        raise ImproperlyConfigured(f"Staging environment requires {setting} to be set")