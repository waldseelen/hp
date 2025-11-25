"""
Production settings for portfolio project.
All security settings enabled, DEBUG=False, production-grade configurations.
Optimized for Google Cloud Run deployment.
"""

import os

from .base import *  # noqa: F401, F403

# Production settings - Override base.py defaults
DEBUG = False

# ==========================================================================
# ALLOWED_HOSTS - Cloud Run Compatible
# ==========================================================================
# Cloud Run provides dynamic URLs like *.run.app
# Also allow custom domains via environment variable
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default=".run.app,.a.run.app,localhost,127.0.0.1",
    cast=lambda v: [s.strip() for s in v.split(",") if s.strip()],
)

# ==========================================================================
# CSRF TRUSTED ORIGINS - Cloud Run Compatible
# ==========================================================================
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="https://*.run.app,https://*.a.run.app",
    cast=lambda v: [s.strip() for s in v.split(",") if s.strip()],
)

# Production database with connection pooling
if dj_database_url:
    DATABASES = {
        "default": dj_database_url.config(
            default=config(
                "DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
            ),
            conn_max_age=600,  # Keep connections alive for 10 minutes
            conn_health_checks=True,  # Validate connections before use
        )
    }
else:
    # Fallback database configuration (SQLite for simple deployments)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
            "OPTIONS": {
                "timeout": 20,
            },
        }
    }

# Static files for production
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# ==========================================================================
# PRODUCTION SECURITY SETTINGS
# ==========================================================================
# XSS Protection
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# ==========================================================================
# SSL/HTTPS SETTINGS - Cloud Run Compatible
# ==========================================================================
# Cloud Run handles SSL termination, so we disable Django's SSL redirect
# to avoid redirect loops. Cloud Run always serves HTTPS externally.
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=False, cast=bool)

# HTTP Strict Transport Security (HSTS)
# Enable HSTS since Cloud Run serves HTTPS
SECURE_HSTS_SECONDS = config(
    "SECURE_HSTS_SECONDS", default=31536000, cast=int
)  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = config(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True, cast=bool
)
SECURE_HSTS_PRELOAD = config("SECURE_HSTS_PRELOAD", default=True, cast=bool)

# Cookie Security
SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", default=True, cast=bool)
CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", default=True, cast=bool)
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"  # Changed from Strict for Cloud Run compatibility
CSRF_COOKIE_SAMESITE = "Lax"

# Proxy SSL Header (CRITICAL for Cloud Run)
# Cloud Run sends X-Forwarded-Proto header to indicate original protocol
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Trust the proxy (Cloud Run load balancer)
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# ==========================================================================
# TEMPLATE CACHING
# ==========================================================================
TEMPLATES[0]["APP_DIRS"] = False
TEMPLATES[0]["OPTIONS"]["loaders"] = [
    (
        "django.template.loaders.cached.Loader",
        [
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
        ],
    ),
]

# ==========================================================================
# EMAIL CONFIGURATION
# ==========================================================================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")

# ==========================================================================
# REDIS CACHE CONFIGURATION (Production)
# ==========================================================================
REDIS_URL = config("REDIS_URL", default="")
if REDIS_URL:
    try:
        import django_redis  # noqa: F401
        CACHES = {
            "default": {
                "BACKEND": "django_redis.cache.RedisCache",
                "LOCATION": REDIS_URL,
                "OPTIONS": {
                    "CLIENT_CLASS": "django_redis.client.DefaultClient",
                    "CONNECTION_POOL_KWARGS": {
                        "max_connections": 20,
                        "retry_on_timeout": True,
                    },
                },
                "KEY_PREFIX": "portfolio",
                "VERSION": 1,
                "TIMEOUT": 3600,
            }
        }
        SESSION_ENGINE = "django.contrib.sessions.backends.cache"
        SESSION_CACHE_ALIAS = "default"
    except ImportError:
        pass  # Fall back to default cache from base.py

# ==========================================================================
# PRODUCTION LOGGING - Console Only (Cloud Run Compatible)
# ==========================================================================
# Cloud Run captures stdout/stderr, so we log to console only.
# File-based logging is NOT recommended in containerized environments.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "json": {
            "format": '{"level": "%(levelname)s", "time": "%(asctime)s", "module": "%(module)s", "message": "%(message)s"}',
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "gunicorn.error": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "gunicorn.access": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# ==========================================================================
# SENTRY ERROR TRACKING (Optional)
# ==========================================================================
SENTRY_DSN = config("SENTRY_DSN", default="")
if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[DjangoIntegration()]
            traces_sample_rate=0.1,
            send_default_pii=False,
            environment="production",
        )
    except ImportError:
        pass  # Sentry not installed

# ==========================================================================
# WHITENOISE STATIC FILES (Production)
# ==========================================================================
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
WHITENOISE_MAX_AGE = 31536000  # 1 year

# ==========================================================================
# CORS SETTINGS (Production)
# ==========================================================================
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="",
    cast=lambda v: [s.strip() for s in v.split(",") if s.strip()],
)