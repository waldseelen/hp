"""
Django settings for portfolio_site project.
"""

import logging.config
import os
from pathlib import Path

from decouple import config

# Optional imports for production
try:
    import dj_database_url
except ImportError:
    dj_database_url = None

# Optional imports for production
try:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration

    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

    # Create dummy classes if sentry is not available
    class DjangoIntegration:
        def __init__(self, **kwargs):
            pass

    class LoggingIntegration:
        def __init__(self, **kwargs):
            pass


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("SECRET_KEY", default="your-secret-key-here")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS", default="*", cast=lambda v: [s.strip() for s in v.split(",")]
)

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django.contrib.humanize",
    # Third party apps
    "rest_framework",
    "corsheaders",
    # Local apps
    "apps.core",
    "apps.main",
    "apps.blog",
    "apps.portfolio",  # Portfolio models (Admin, UserSession, GDPR, Analytics, etc.)
    "apps.tools",
    "apps.contact",
    "apps.chat",
    "apps.playground",
    "apps.ai_optimizer",
]

# Optional third-party apps (add if installed)
OPTIONAL_APPS = [
    "django_extensions",
    "channels",
]

for app in OPTIONAL_APPS:
    try:
        __import__(app)
        INSTALLED_APPS.append(app)
    except ImportError:
        pass

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "apps.main.ratelimit.RateLimitMiddleware",  # Global rate limiting
    "apps.main.middleware.SecurityHeadersMiddleware",  # Custom security headers with CSP
    "apps.main.middleware.static_optimization_middleware.TTFBOptimizationMiddleware",  # TTFB optimization
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "apps.main.middleware.static_optimization_middleware.StaticFileOptimizationMiddleware",  # Static file optimization
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.main.ratelimit.APIRateLimitMiddleware",  # API-specific rate limiting
    "apps.core.middleware.api_caching.APICachingMiddleware",  # API response caching with ETag
    "apps.core.middleware.api_caching.CacheInvalidationMiddleware",  # Cache invalidation on updates
    "apps.core.middleware.api_caching.ResponseTimeMiddleware",  # Response time tracking
    "apps.main.middleware.CacheControlMiddleware",  # Cache control headers
    "apps.main.middleware.CompressionMiddleware",  # Compression optimization
    "apps.main.middleware.PerformanceMiddleware",  # Performance monitoring
    "apps.main.middleware.apm_middleware.APMMiddleware",  # APM transaction tracking
    "apps.main.middleware.apm_middleware.DatabaseQueryTrackingMiddleware",  # Database query tracking
    "apps.main.middleware.static_optimization_middleware.ResourceHintsMiddleware",  # Resource hints
    "apps.main.middleware.static_optimization_middleware.StaticFileMetricsMiddleware",  # Static file metrics
]

ROOT_URLCONF = "project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.main.context_processors.global_context",
                "apps.main.context_processors.breadcrumbs",
                "apps.main.context_processors.language_context",
                "apps.main.context_processors.csp_nonce",
            ],
        },
    },
]

WSGI_APPLICATION = "project.wsgi.application"

# Database
# Use DATABASE_URL environment variable for PostgreSQL, fallback to SQLite
# Database configuration
if dj_database_url:
    DATABASES = {
        "default": dj_database_url.config(
            default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}", conn_max_age=600
        )
    }
else:
    # Fallback for development without dj_database_url
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Channel Layers Configuration
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [config("REDIS_URL", default="redis://localhost:6379/0")],
            "capacity": 1500,  # Maximum number of messages to store
            "expiry": 60,  # Message expiry time in seconds
            "group_expiry": 86400,  # Group membership expiry (24 hours)
            "symmetric_encryption_keys": [SECRET_KEY],
        },
    },
}

# ASGI Application
ASGI_APPLICATION = "project.asgi.application"

# Note: Celery configuration removed (not needed for portfolio/blog site)
# For scheduled tasks, consider using django-cron or APScheduler as lightweight alternatives

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
from django.utils.translation import gettext_lazy as _

LANGUAGE_CODE = "tr"
LANGUAGES = [
    ("tr", _("Turkish")),
    ("en", _("English")),
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

TIME_ZONE = "Europe/Istanbul"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = BASE_DIR / "staticfiles"

# WhiteNoise configuration for static files
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Static file optimization settings
STATIC_COMPRESSION = True
STATIC_WEBP_SUPPORT = True
WHITENOISE_MAX_AGE = 31536000  # 1 year for static files
WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_ALLOW_ALL_ORIGINS = True
WHITENOISE_SKIP_COMPRESS_EXTENSIONS = (
    "jpg",
    "jpeg",
    "png",
    "gif",
    "webp",
    "zip",
    "gz",
    "tgz",
    "bz2",
    "tbz",
    "xz",
    "br",
    "swf",
    "flv",
    "woff",
    "woff2",
)
WHITENOISE_ADD_HEADERS_FUNCTION = "whitenoise.middleware.add_headers_function"
WHITENOISE_AUTOREFRESH = False  # Disable in production
WHITENOISE_USE_FINDERS = False  # Use STATIC_ROOT only
WHITENOISE_INDEX_FILE = True  # Serve index.html for directories

# CDN Configuration
CDN_ENABLED = config("CDN_ENABLED", default=False, cast=bool)
CDN_DOMAIN = config("CDN_DOMAIN", default="")

# If CDN is enabled, use CDN domain for static files
if CDN_ENABLED and CDN_DOMAIN:
    STATIC_URL = f"https://{CDN_DOMAIN}/static/"

# Image optimization settings
IMAGE_LAZY_LOADING = True
IMAGE_WEBP_CONVERSION = True
IMAGE_QUALITY_COMPRESSION = 85

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# API Configuration
API_VERSION = "v1"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CORS settings - SECURE: Only allow specific origins
CORS_ALLOW_ALL_ORIGINS = config("CORS_ALLOW_ALL_ORIGINS", default=False, cast=bool)
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="",
    cast=lambda v: [s.strip() for s in v.split(",") if s.strip()],
)
CORS_ALLOW_CREDENTIALS = True

# REST Framework settings
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# CSRF Trusted Origins (for Railway and custom domains)
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="https://*.railway.app",
    cast=lambda v: [s.strip() for s in v.split(",") if s.strip()],
)

# Session configuration
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# Logging configuration
# Basic logging removed - using advanced configuration below

# Cache configuration
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}

# Email configuration (for contact forms, etc.)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Admin configuration for error reporting
ADMINS = [
    ("Admin", config("ADMIN_EMAIL", default="admin@localhost")),
]
MANAGERS = ADMINS

# Custom User Model
AUTH_USER_MODEL = "main.Admin"

# Authentication backends
AUTHENTICATION_BACKENDS = [
    "apps.main.auth_backends.RestrictedAdminBackend",
]

# ==========================================================================
# SENTRY MONITORING AND ERROR TRACKING
# ==========================================================================

SENTRY_DSN = config("SENTRY_DSN", default="")

# Performance budget configuration for APM
PERFORMANCE_BUDGETS = {
    "SLOW_TRANSACTION_THRESHOLD": config(
        "SLOW_TRANSACTION_THRESHOLD", default=2.0, cast=float
    ),  # seconds
    "VERY_SLOW_THRESHOLD": config(
        "VERY_SLOW_THRESHOLD", default=5.0, cast=float
    ),  # seconds
    "DATABASE_QUERY_THRESHOLD": config(
        "DB_QUERY_THRESHOLD", default=0.1, cast=float
    ),  # seconds
    "CACHE_OPERATION_THRESHOLD": config(
        "CACHE_THRESHOLD", default=0.05, cast=float
    ),  # seconds
    "API_RESPONSE_THRESHOLD": config(
        "API_THRESHOLD", default=1.0, cast=float
    ),  # seconds
}


def filter_slow_transactions(event, hint):
    """
    Custom filter for Sentry transactions to focus on performance issues
    """
    try:
        # Only process transaction events
        if event.get("type") != "transaction":
            return event

        transaction_duration = event.get("timestamp", 0) - event.get(
            "start_timestamp", 0
        )
        transaction_name = event.get("transaction", "unknown")

        # Always capture very slow transactions
        if transaction_duration > PERFORMANCE_BUDGETS["VERY_SLOW_THRESHOLD"]:
            event["tags"] = event.get("tags", {})
            event["tags"]["performance_issue"] = "very_slow"
            event["tags"]["budget_exceeded"] = "critical"
            return event

        # Capture moderately slow transactions with sampling
        elif transaction_duration > PERFORMANCE_BUDGETS["SLOW_TRANSACTION_THRESHOLD"]:
            event["tags"] = event.get("tags", {})
            event["tags"]["performance_issue"] = "slow"
            event["tags"]["budget_exceeded"] = "warning"
            # Sample slow transactions at higher rate
            import random

            if random.random() < 0.5:  # 50% sampling for slow transactions
                return event
            else:
                return None

        # For normal speed transactions, use default sampling
        return event

    except Exception as e:
        # If filtering fails, return the event to ensure it's still captured
        logging.getLogger(__name__).error(f"Error in Sentry transaction filter: {e}")
        return event


if SENTRY_AVAILABLE and SENTRY_DSN:
    try:
        # Initialize Sentry SDK only if DSN is provided
        sentry_logging = LoggingIntegration(
            level=logging.INFO,  # Capture info and above as breadcrumbs
            event_level=logging.ERROR,  # Send errors as events
        )

        # Import additional APM integrations (Celery removed)
        from sentry_sdk.integrations.redis import RedisIntegration

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[
                DjangoIntegration(
                    transaction_style="url",
                    middleware_spans=True,
                    signals_spans=True,
                    cache_spans=True,
                ),
                sentry_logging,
                RedisIntegration(),
            ],
            traces_sample_rate=config(
                "SENTRY_TRACES_SAMPLE_RATE", default=0.2, cast=float
            ),
            profiles_sample_rate=config(
                "SENTRY_PROFILES_SAMPLE_RATE", default=0.1, cast=float
            ),
            send_default_pii=False,
            debug=DEBUG,
            environment=config("ENVIRONMENT", default="development"),
            release=config("APP_VERSION", default="1.0.0"),
            # Performance monitoring configuration
            enable_tracing=True,
            # Custom performance budget configuration
            before_send_transaction=lambda event, hint: filter_slow_transactions(
                event, hint
            ),
            # Additional APM settings
            max_breadcrumbs=100,
            attach_stacktrace=True,
            request_bodies="medium",
        )

        # Test Sentry connection
        import sentry_sdk

        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("initialization", "success")

    except Exception as e:
        import warnings

        warnings.warn(f"Sentry initialization failed ({e}), error tracking disabled")
elif SENTRY_DSN and not SENTRY_AVAILABLE:
    import warnings

    warnings.warn(
        "SENTRY_DSN provided but sentry-sdk not installed. Install with: pip install sentry-sdk"
    )

# ==========================================================================
# ADVANCED LOGGING CONFIGURATION
# ==========================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
        "json": {
            "format": '{"level": "%(levelname)s", "time": "%(asctime)s", "module": "%(module)s", "message": "%(message)s"}',
        },
        "structured_json": {
            "()": "apps.main.logging.json_formatter.StructuredJSONFormatter",
            "service_name": config("SERVICE_NAME", default="portfolio_site"),
            "environment": config("ENVIRONMENT", default="development"),
            "include_extra_fields": True,
        },
    },
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
        "request_context": {
            "()": "apps.main.logging.json_formatter.RequestContextFilter",
        },
        "performance_filter": {
            "()": "apps.main.logging.json_formatter.PerformanceFilter",
        },
        "security_filter": {
            "()": "apps.main.logging.json_formatter.SecurityFilter",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "filters": ["require_debug_true"],
        },
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "django.log",
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 10,
            "formatter": "verbose",
            "filters": ["require_debug_false"],
        },
        "structured_json_file": {
            "level": "INFO",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": BASE_DIR / "logs" / "structured.log",
            "when": "midnight",
            "interval": 1,
            "backupCount": 30,  # Keep 30 days
            "formatter": "structured_json",
            "filters": ["request_context", "performance_filter"],
        },
        "performance_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "performance.log",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 5,
            "formatter": "structured_json",
            "filters": ["performance_filter"],
        },
        "error_file": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "errors.log",
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 15,  # Keep more error logs
            "formatter": "structured_json",
            "filters": ["request_context"],
        },
        "security_file": {
            "level": "WARNING",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "security.log",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 20,  # Keep security logs longer
            "formatter": "structured_json",
            "filters": ["security_filter", "request_context"],
        },
        "aggregated_json": {
            "level": "DEBUG",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": BASE_DIR / "logs" / "aggregated.jsonl",
            "when": "H",  # Hourly rotation
            "interval": 1,
            "backupCount": 24 * 7,  # Keep 1 week of hourly logs
            "formatter": "structured_json",
            "filters": ["request_context", "performance_filter", "security_filter"],
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": config("DJANGO_LOG_LEVEL", default="INFO"),
            "propagate": False,
        },
        "django.request": {
            "handlers": ["error_file"],
            "level": "ERROR",
            "propagate": True,
        },
        "main.performance": {
            "handlers": ["performance_file"],
            "level": "INFO",
            "propagate": False,
        },
        "main.security": {
            "handlers": ["error_file"],
            "level": "WARNING",
            "propagate": True,
        },
    },
}

# Create logs directory if it doesn't exist
logs_dir = BASE_DIR / "logs"
logs_dir.mkdir(exist_ok=True)

# ==========================================================================
# PUSH NOTIFICATIONS CONFIGURATION
# ==========================================================================

# VAPID Keys for Web Push
WEBPUSH_SETTINGS = {
    "VAPID_PUBLIC_KEY": config("VAPID_PUBLIC_KEY", default=""),
    "VAPID_PRIVATE_KEY": config("VAPID_PRIVATE_KEY", default=""),
    "VAPID_ADMIN_EMAIL": config("VAPID_ADMIN_EMAIL", default="admin@example.com"),
}

# ==========================================================================
# PERFORMANCE MONITORING SETTINGS
# ==========================================================================

# Performance monitoring
PERFORMANCE_MONITORING = {
    "ENABLED": config("PERFORMANCE_MONITORING_ENABLED", default=True, cast=bool),
    "SAMPLE_RATE": config("PERFORMANCE_SAMPLE_RATE", default=0.1, cast=float),
    "TRACK_SQL_QUERIES": config("TRACK_SQL_QUERIES", default=DEBUG, cast=bool),
    "MAX_QUERY_TIME": config("MAX_QUERY_TIME", default=0.1, cast=float),
    "TRACK_CACHE_HITS": config("TRACK_CACHE_HITS", default=True, cast=bool),
}

# Core Web Vitals thresholds
CORE_WEB_VITALS = {
    "LCP_THRESHOLD": 2.5,  # Largest Contentful Paint (seconds)
    "FID_THRESHOLD": 0.1,  # First Input Delay (seconds)
    "CLS_THRESHOLD": 0.1,  # Cumulative Layout Shift
    "INP_THRESHOLD": 0.2,  # Interaction to Next Paint (seconds)
    "TTFB_THRESHOLD": 0.8,  # Time to First Byte (seconds)
}

# ==========================================================================
# SECURITY ENHANCEMENTS
# ==========================================================================

# Content Security Policy with Nonces
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = (
    "'self'",
    "'nonce-{nonce}'",
    "https://unpkg.com",
    "https://cdn.jsdelivr.net",
)
CSP_STYLE_SRC = (
    "'self'",
    "'nonce-{nonce}'",
    "https://fonts.googleapis.com",
    "https://unpkg.com",
)
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_CONNECT_SRC = ("'self'", "https://api.github.com", "wss:", "https:")
CSP_FRAME_ANCESTORS = ("'none'",)
CSP_FRAME_SRC = ("'self'", "https://www.youtube.com", "https://player.vimeo.com")
CSP_WORKER_SRC = ("'self'", "blob:")
CSP_MANIFEST_SRC = ("'self'",)

# Enable CSP reporting
CSP_REPORT_ONLY = config("CSP_REPORT_ONLY", default=False, cast=bool)
CSP_REPORT_URI = "/csp-report/"

# Nonce settings
CSP_INCLUDE_NONCE_IN = ["script-src", "style-src"]

# Rate limiting
RATELIMIT_ENABLE = config("RATELIMIT_ENABLE", default=True, cast=bool)
RATELIMIT_USE_CACHE = "default"

# API rate limits
API_RATE_LIMITS = {
    "performance": "100/h",  # Performance metrics endpoint
    "webpush": "10/m",  # Push notification endpoints
    "contact": "5/m",  # Contact form
    "default": "60/m",  # Default for other endpoints
}

# ==========================================================================
# EMAIL CONFIGURATION
# ==========================================================================

if not DEBUG:
    EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
    EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")

    if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
        try:
            EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
            EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
            EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
            EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
            EMAIL_HOST_USER = EMAIL_HOST_USER
            EMAIL_HOST_PASSWORD = EMAIL_HOST_PASSWORD
            DEFAULT_FROM_EMAIL = config(
                "DEFAULT_FROM_EMAIL", default="noreply@example.com"
            )
            SERVER_EMAIL = config("SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)

            # Test email configuration
            import smtplib
            from email.mime.text import MIMEText

            # Note: Actual SMTP test is expensive, so we'll skip it here

        except Exception as e:
            import warnings

            warnings.warn(
                f"Email configuration failed ({e}), falling back to console backend"
            )
            EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    else:
        import warnings

        warnings.warn(
            "EMAIL_HOST_USER and EMAIL_HOST_PASSWORD not provided, using console email backend"
        )
        EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ==========================================================================
# REDIS CACHE CONFIGURATION (Production & Development)
# ==========================================================================

# Try to import django_redis (optional dependency)
try:
    import django_redis  # noqa: F401

    DJANGO_REDIS_AVAILABLE = True
except ImportError:
    DJANGO_REDIS_AVAILABLE = False

REDIS_URL = config("REDIS_URL", default="redis://localhost:6379/1")

if REDIS_URL and DJANGO_REDIS_AVAILABLE:
    try:
        # Test Redis connection
        import redis

        r = redis.from_url(REDIS_URL)
        r.ping()

        # Multi-tier cache configuration
        CACHES = {
            # Default cache for general purpose
            "default": {
                "BACKEND": "django_redis.cache.RedisCache",
                "LOCATION": REDIS_URL,
                "OPTIONS": {
                    "CLIENT_CLASS": "django_redis.client.DefaultClient",
                    "CONNECTION_POOL_KWARGS": {
                        "max_connections": 50,
                        "retry_on_timeout": True,
                        "socket_keepalive": True,
                        "socket_keepalive_options": {
                            1: 1,  # TCP_KEEPIDLE
                            2: 1,  # TCP_KEEPINTVL
                            3: 5,  # TCP_KEEPCNT
                        },
                    },
                    "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
                    "SERIALIZER": "django_redis.serializers.json.JSONSerializer",
                    "IGNORE_EXCEPTIONS": True,  # Don't crash on Redis errors
                },
                "KEY_PREFIX": "portfolio" if not DEBUG else "portfolio-dev",
                "VERSION": 1,
                "TIMEOUT": 3600,  # 1 hour default timeout
            },
            # Cache for database query results (shorter TTL)
            "query_cache": {
                "BACKEND": "django_redis.cache.RedisCache",
                "LOCATION": REDIS_URL,
                "OPTIONS": {
                    "CLIENT_CLASS": "django_redis.client.DefaultClient",
                    "CONNECTION_POOL_KWARGS": {
                        "max_connections": 30,
                        "retry_on_timeout": True,
                    },
                    "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
                    "IGNORE_EXCEPTIONS": True,
                },
                "KEY_PREFIX": "query" if not DEBUG else "query-dev",
                "VERSION": 1,
                "TIMEOUT": 300,  # 5 minutes for queries
            },
            # Cache for API responses
            "api_cache": {
                "BACKEND": "django_redis.cache.RedisCache",
                "LOCATION": REDIS_URL,
                "OPTIONS": {
                    "CLIENT_CLASS": "django_redis.client.DefaultClient",
                    "CONNECTION_POOL_KWARGS": {
                        "max_connections": 20,
                        "retry_on_timeout": True,
                    },
                    "IGNORE_EXCEPTIONS": True,
                },
                "KEY_PREFIX": "api" if not DEBUG else "api-dev",
                "VERSION": 1,
                "TIMEOUT": 600,  # 10 minutes for API responses
            },
            # Cache for template fragments (longer TTL)
            "template_cache": {
                "BACKEND": "django_redis.cache.RedisCache",
                "LOCATION": REDIS_URL,
                "OPTIONS": {
                    "CLIENT_CLASS": "django_redis.client.DefaultClient",
                    "CONNECTION_POOL_KWARGS": {
                        "max_connections": 10,
                        "retry_on_timeout": True,
                    },
                    "IGNORE_EXCEPTIONS": True,
                },
                "KEY_PREFIX": "template" if not DEBUG else "template-dev",
                "VERSION": 1,
                "TIMEOUT": 7200,  # 2 hours for templates
            },
        }

        # Session storage in Redis
        SESSION_ENGINE = "django.contrib.sessions.backends.cache"
        SESSION_CACHE_ALIAS = "default"
        SESSION_COOKIE_AGE = 1209600  # 2 weeks

        # Cache key configuration
        CACHE_MIDDLEWARE_ALIAS = "default"
        CACHE_MIDDLEWARE_SECONDS = 600
        CACHE_MIDDLEWARE_KEY_PREFIX = "middleware"

    except Exception as e:
        import warnings

        warnings.warn(
            f"Redis connection failed ({e}), falling back to local memory cache"
        )
        DJANGO_REDIS_AVAILABLE = False

# Fallback to local memory cache if Redis is not available
if not DJANGO_REDIS_AVAILABLE or not REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "unique-snowflake-fallback",
            "TIMEOUT": 300,
        },
        "query_cache": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "query-cache",
            "TIMEOUT": 300,
        },
        "api_cache": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "api-cache",
            "TIMEOUT": 600,
        },
        "template_cache": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "template-cache",
            "TIMEOUT": 7200,
        },
    }

# ==========================================================================
# CUSTOM SETTINGS
# ==========================================================================

SITE_NAME = config("SITE_NAME", default="Professional Portfolio")
SITE_DESCRIPTION = config(
    "SITE_DESCRIPTION", default="Full Stack Developer & Cybersecurity Enthusiast"
)

# Feature flags
FEATURES = {
    "PWA_ENABLED": config("PWA_ENABLED", default=True, cast=bool),
    "PUSH_NOTIFICATIONS": config("PUSH_NOTIFICATIONS", default=True, cast=bool),
    "PERFORMANCE_MONITORING": config("PERFORMANCE_MONITORING", default=True, cast=bool),
    "ANALYTICS_ENABLED": config("ANALYTICS_ENABLED", default=True, cast=bool),
    "SERVICE_WORKER_ENABLED": config("SERVICE_WORKER_ENABLED", default=True, cast=bool),
    "LAZY_LOADING_ENABLED": config("LAZY_LOADING_ENABLED", default=True, cast=bool),
}

# Image optimization settings
IMAGE_OPTIMIZATION = {
    "ENABLED": config("IMAGE_OPTIMIZATION_ENABLED", default=True, cast=bool),
    "WEBP_QUALITY": config("WEBP_QUALITY", default=80, cast=int),
    "AVIF_QUALITY": config("AVIF_QUALITY", default=75, cast=int),
    "JPEG_QUALITY": config("JPEG_QUALITY", default=85, cast=int),
    "PNG_QUALITY": config("PNG_QUALITY", default=90, cast=int),
    "MAX_WIDTH": config("MAX_IMAGE_WIDTH", default=2000, cast=int),
    "MAX_HEIGHT": config("MAX_IMAGE_HEIGHT", default=2000, cast=int),
}

# ==========================================================================
# EXTERNAL SERVICES & CDN CONFIGURATION
# ==========================================================================
# Centralized configuration for external service URLs to eliminate hardcoded values

EXTERNAL_SERVICES = {
    # Google Services
    "google_fonts": config("GOOGLE_FONTS_URL", default="https://fonts.googleapis.com"),
    "google_fonts_static": config(
        "GOOGLE_FONTS_STATIC_URL", default="https://fonts.gstatic.com"
    ),
    "google_pagespeed_api": "https://www.googleapis.com/pagespeedapi/v5/runPagespeed",
    "google_analytics": config("GOOGLE_ANALYTICS_URL", default=""),
    # CDN Services
    "cdn_tailwind": config("CDN_TAILWIND_URL", default="https://cdn.tailwindcss.com"),
    "cdn_jsdelivr": config("CDN_JSDELIVR_URL", default="https://cdn.jsdelivr.net"),
    "cdn_unpkg": config("CDN_UNPKG_URL", default="https://unpkg.com"),
    "cdn_cloudflare": config(
        "CDN_CLOUDFLARE_URL", default="https://cdnjs.cloudflare.com"
    ),
    # Social Media URLs (should be overridden via environment variables)
    "social_github": config(
        "SOCIAL_GITHUB_URL", default="https://github.com/bugraakin"
    ),
    "social_linkedin": config(
        "SOCIAL_LINKEDIN_URL", default="https://linkedin.com/in/bugraak"
    ),
    "social_twitter": config(
        "SOCIAL_TWITTER_URL", default="https://twitter.com/bugraakin"
    ),
    "social_cal": config("SOCIAL_CAL_URL", default="https://cal.com/bugraakin"),
    # API Services
    "github_api": "https://api.github.com",
    "spotify_embed": "https://open.spotify.com/embed",
    # Other Services
    "perplexity_cdn": "https://r2cdn.perplexity.ai",
    "pagespeed_web": "https://pagespeed.web.dev",
}

# Schema.org context URL (for structured data)
SCHEMA_ORG_CONTEXT = "https://schema.org"

# PageSpeed API Key (optional, for performance monitoring)
PAGESPEED_API_KEY = config("PAGESPEED_API_KEY", default="")
