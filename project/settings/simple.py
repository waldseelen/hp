"""
Simple Django settings - Just the basics that work
"""

import os
from pathlib import Path

# This gets us to project root: D:\FILES\BEST
BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = "django-insecure-but-working-key-for-development"

DEBUG = True

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Local apps - only the ones that exist and work
    "apps.core",  # Core middleware and utilities
    "apps.main",
    "apps.blog",
    "apps.tools",
    "apps.contact",
    "apps.chat",
    "apps.playground",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Performance & Optimization Middleware
    "apps.core.middleware.api_caching.APICachingMiddleware",
    "apps.core.middleware.api_caching.CacheInvalidationMiddleware",
    "apps.core.middleware.api_caching.ResponseTimeMiddleware",
    "apps.main.middleware.CacheControlMiddleware",  # From apps/main/middleware.py
    "apps.main.middleware.CompressionMiddleware",  # From apps/main/middleware.py
    "apps.main.middleware.PerformanceMiddleware",  # From apps/main/middleware.py
    "apps.main.middleware.apm_middleware.APMMiddleware",  # From apps/main/middleware/apm_middleware.py
    "apps.main.middleware.apm_middleware.DatabaseQueryTrackingMiddleware",  # From apps/main/middleware/apm_middleware.py
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
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.main.context_processors.social_links",
                "apps.main.context_processors.global_context",
                "apps.main.context_processors.breadcrumbs",
                "apps.main.context_processors.language_context",
                "apps.main.context_processors.csp_nonce",
            ],
        },
    },
]

WSGI_APPLICATION = "project.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

LANGUAGE_CODE = "tr-tr"
TIME_ZONE = "Europe/Istanbul"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# API Configuration
API_VERSION = "v1"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Simple cache - Local memory cache for development
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
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

# Console email for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Performance Budgets Configuration for APM
PERFORMANCE_BUDGETS = {
    "SLOW_TRANSACTION_THRESHOLD": 2.0,  # seconds
    "VERY_SLOW_THRESHOLD": 5.0,  # seconds
    "DATABASE_QUERY_THRESHOLD": 0.1,  # seconds
    "CACHE_OPERATION_THRESHOLD": 0.05,  # seconds
    "API_RESPONSE_THRESHOLD": 1.0,  # seconds
}

# Authentication: restrict to single admin account via custom backend
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",  # Enable standard DB login
]

# Custom User Model (matches base.py)
AUTH_USER_MODEL = "main.Admin"

# Session cookie hardening (still okay in DEBUG for local dev)
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# Authentication redirects and session hardening
LOGIN_URL = "admin:login"
LOGIN_REDIRECT_URL = "admin:index"
LOGOUT_REDIRECT_URL = "admin:login"

SESSION_COOKIE_AGE = 60 * 60  # 1 hour
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_REFERRER_POLICY = "same-origin"
