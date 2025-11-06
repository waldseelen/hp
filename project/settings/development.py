"""
Development settings for portfolio project
Enhanced with fix all.yml optimizations
"""

import os

from .base import *

# Development settings
DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# ==========================================================================
# DEVELOPMENT ENVIRONMENT OPTIMIZATIONS (from fix all.yml)
# ==========================================================================

# Development server environment variables
os.environ.setdefault("DJANGO_DEBUG", "True")
os.environ.setdefault("DJANGO_DEVELOPMENT_SERVER", "True")

# Template optimization for development
TEMPLATES[0]["OPTIONS"]["context_processors"].extend(
    [
        "django.template.context_processors.debug",
    ]
)

# Enable template debugging
TEMPLATES[0]["OPTIONS"]["debug"] = True

# Disable template caching for development
TEMPLATES[0]["OPTIONS"]["loaders"] = [
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
]

# Database for development
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Static files
STATIC_URL = "/static/"
STATICFILES_DIRS = [
    BASE_DIR.parent / "static",
]

# Development email backend
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Development cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}

# Development logging with enhanced error monitoring
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "verbose",
        },
        "template_errors": {
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "template_errors_dev.log",
            "level": "ERROR",
            "formatter": "verbose",
        },
        "server_management": {
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "server_management_dev.log",
            "level": "INFO",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "main.template_errors": {
            "handlers": ["template_errors", "console"],
            "level": "ERROR",
            "propagate": False,
        },
        "main.server_management": {
            "handlers": ["server_management", "console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.template": {
            "handlers": ["template_errors", "console"],
            "level": "ERROR",
            "propagate": True,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
}

# Development auto-detection
DEVELOPMENT_AUTO_DETECTION = {
    "DETECT_DJANGO_PROJECT": True,
    "FIND_MANAGE_PY": True,
    "DETECT_SETTINGS_MODULE": True,
}

# Development optimization settings
DEVELOPMENT_OPTIMIZATION = {
    "CACHE_TEMPLATES": False,  # Disable template caching
    "AUTO_RELOAD": True,  # Enable auto-reload
    "DEBUG_TOOLBAR": DEBUG,  # Enable debug toolbar in debug mode
}

# Development security settings
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# ==========================================================================
# DJANGO DEBUG TOOLBAR CONFIGURATION
# ==========================================================================
if DEBUG:
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE
    INTERNAL_IPS = ["127.0.0.1", "localhost"]

    # Debug Toolbar Settings
    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG,
        "DISABLE_PANELS": [],
        "INSERT_BEFORE": "</body>",
        "RENDER_PANELS": True,
        "SHOW_TEMPLATE_CONTEXT": True,
        "SQL_WARNING_THRESHOLD": 100,  # Milliseconds
    }

    # Enable all panels for comprehensive analysis
    DEBUG_TOOLBAR_PANELS = [
        "debug_toolbar.panels.history.HistoryPanel",
        "debug_toolbar.panels.versions.VersionsPanel",
        "debug_toolbar.panels.timer.TimerPanel",
        "debug_toolbar.panels.settings.SettingsPanel",
        "debug_toolbar.panels.headers.HeadersPanel",
        "debug_toolbar.panels.request.RequestPanel",
        "debug_toolbar.panels.sql.SQLPanel",  # Most important for query optimization
        "debug_toolbar.panels.staticfiles.StaticFilesPanel",
        "debug_toolbar.panels.templates.TemplatesPanel",
        "debug_toolbar.panels.cache.CachePanel",
        "debug_toolbar.panels.signals.SignalsPanel",
        "debug_toolbar.panels.redirects.RedirectsPanel",
        "debug_toolbar.panels.profiling.ProfilingPanel",
    ]
