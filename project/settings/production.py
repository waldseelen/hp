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
# ALLOWED_HOSTS - Add Cloud Run domains
# ==========================================================================
# Get hosts from environment variable and add Cloud Run domain pattern
_allowed_hosts_raw = os.environ.get("ALLOWED_HOSTS", "")
_allowed_hosts_env = (
    [host.strip() for host in _allowed_hosts_raw.split(",") if host.strip()]
    if _allowed_hosts_raw
    else []
)
ALLOWED_HOSTS = _allowed_hosts_env.copy()

# Add Cloud Run domain pattern
if ".run.app" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(".run.app")

# ==========================================================================
# CSRF_TRUSTED_ORIGINS - Add Cloud Run domains for CSRF protection
# ==========================================================================
# Get origins from environment variable
_csrf_origins_raw = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
_csrf_origins_env = (
    [origin.strip() for origin in _csrf_origins_raw.split(",") if origin.strip()]
    if _csrf_origins_raw
    else []
)
CSRF_TRUSTED_ORIGINS = _csrf_origins_env.copy()

# Add Cloud Run origins
_cloud_run_origins = [
    "https://*.run.app",
]

for origin in _cloud_run_origins:
    if origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)

# ==========================================================================
# SECURITY SETTINGS - Production hardening
# ==========================================================================
# Force HTTPS in production
SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "True").lower() == "true"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Session and CSRF cookies security
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# HSTS settings
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Other security headers
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"