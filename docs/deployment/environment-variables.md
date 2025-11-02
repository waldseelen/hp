# Environment Variables Documentation

**Last Updated:** 2025-11-01
**Phase:** 20 - Security Hardening
**Status:** Production Ready

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Core Django Settings](#core-django-settings)
3. [Database Configuration](#database-configuration)
4. [Cache & Redis Configuration](#cache--redis-configuration)
5. [Email/SMTP Configuration](#emailsmtp-configuration)
6. [Security Settings](#security-settings)
7. [CDN & External Services](#cdn--external-services)
8. [API Keys & Secrets](#api-keys--secrets)
9. [Monitoring & Logging](#monitoring--logging)
10. [Feature Flags](#feature-flags)
11. [Environment-Specific Examples](#environment-specific-examples)

---

## Quick Start

1. **Copy the template:**
   ```bash
   cp .env.example .env
   ```

2. **Required variables (minimum for development):**
   ```bash
   SECRET_KEY=your-generated-secret-key
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   ```

3. **Generate SECRET_KEY:**
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

---

## Core Django Settings

### `SECRET_KEY` (REQUIRED)
**Type:** String (50+ characters)
**Description:** Cryptographic signing key for Django. NEVER share or commit this value.

**Generate:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Example:**
```bash
SECRET_KEY=django-insecure-abc123xyz789-your-unique-key-here
```

**⚠️ Security Notes:**
- Use different keys for development, staging, and production
- Rotate keys if compromised
- Store in secure vault (e.g., AWS Secrets Manager, Vault)

---

### `DEBUG`
**Type:** Boolean
**Default:** `False`
**Description:** Enable/disable debug mode. **MUST be `False` in production.**

**Examples:**
```bash
# Development
DEBUG=True

# Production
DEBUG=False
```

**⚠️ Warning:** Running with `DEBUG=True` in production exposes:
- Stack traces and sensitive data
- Django Debug Toolbar
- Source code information

---

### `ALLOWED_HOSTS`
**Type:** Comma-separated list
**Default:** (empty - must be set)
**Description:** List of host/domain names Django can serve.

**Examples:**
```bash
# Development
ALLOWED_HOSTS=localhost,127.0.0.1

# Production (single domain)
ALLOWED_HOSTS=example.com,.example.com

# Production (multiple domains)
ALLOWED_HOSTS=example.com,.example.com,www.example.com

# Platform-specific
ALLOWED_HOSTS=.railway.app,.vercel.app,example.com
```

**Pattern Matching:**
- `.example.com` - matches `example.com` and all subdomains
- `*.example.com` - matches only subdomains (not root domain)

---

### `DJANGO_SETTINGS_MODULE`
**Type:** String
**Default:** `project.settings.base`
**Description:** Python path to settings module.

**Options:**
```bash
# Development
DJANGO_SETTINGS_MODULE=project.settings.development

# Production
DJANGO_SETTINGS_MODULE=project.settings.production

# Testing
DJANGO_SETTINGS_MODULE=project.settings.testing
```

---

## Database Configuration

### `DATABASE_URL`
**Type:** Database URL
**Default:** `sqlite:///db.sqlite3`
**Description:** Database connection string (supports PostgreSQL, MySQL, SQLite).

**Format:** `database://user:password@host:port/database_name`

**Examples:**
```bash
# Development (SQLite)
DATABASE_URL=sqlite:///db.sqlite3

# Production (PostgreSQL)
DATABASE_URL=postgresql://username:password@localhost:5432/portfolio_db

# Production (PostgreSQL with SSL)
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require

# Railway PostgreSQL
DATABASE_URL=postgresql://user:pass@containers-us-west-xxx.railway.app:7432/railway

# Heroku PostgreSQL
DATABASE_URL=postgres://user:pass@ec2-xxx.compute-1.amazonaws.com:5432/dbname
```

**⚠️ Security:**
- Use strong passwords (20+ characters, mixed case, symbols)
- Enable SSL/TLS connections (`?sslmode=require`)
- Rotate credentials periodically

---

### `DB_CONN_MAX_AGE`
**Type:** Integer (seconds)
**Default:** `0` (dev), `600` (prod)
**Description:** Database connection pooling - keep connections alive.

**Recommended:**
```bash
# Development (disable pooling)
DB_CONN_MAX_AGE=0

# Production (10 minutes)
DB_CONN_MAX_AGE=600
```

---

## Cache & Redis Configuration

### `REDIS_URL`
**Type:** Redis URL
**Default:** `redis://localhost:6379/0`
**Description:** Redis connection string for caching and sessions.

**Format:** `redis://[:password]@host:port/db`

**Examples:**
```bash
# Local development
REDIS_URL=redis://localhost:6379/0

# Production with password
REDIS_URL=redis://:strongpassword@redis-server:6379/1

# Redis Cloud
REDIS_URL=redis://:password@redis-12345.c123.us-east-1-2.ec2.cloud.redislabs.com:12345

# Railway Redis
REDIS_URL=redis://default:password@containers-us-west-xxx.railway.app:6379
```

**TLS/SSL Support:**
```bash
REDIS_URL=rediss://:password@host:6380/0
```

---

### `CACHE_TIMEOUT`
**Type:** Integer (seconds)
**Default:** `300`
**Description:** Default cache timeout.

```bash
CACHE_TIMEOUT=300  # 5 minutes
CACHE_TIMEOUT=3600  # 1 hour
```

---

## Email/SMTP Configuration

### Email Backend
**Type:** String
**Default:** `django.core.mail.backends.console.EmailBackend`

```bash
# Development (console output)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Production (SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
```

---

### SMTP Settings

```bash
# Gmail
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password

# SendGrid
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=SG.xxxxxxxxxxxxx

# AWS SES
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=AKIAXXXXXXXXXXXXXXXX
EMAIL_HOST_PASSWORD=your-smtp-password

# Default sender
DEFAULT_FROM_EMAIL=noreply@example.com
```

**⚠️ Gmail Users:** Use [App Passwords](https://support.google.com/accounts/answer/185833), not your regular password.

---

## Security Settings

### HTTPS/SSL Enforcement

```bash
# Enable HTTPS redirect (production)
SECURE_SSL_REDIRECT=True

# HTTP Strict Transport Security
SECURE_HSTS_SECONDS=31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

**⚠️ HSTS Warning:** Once enabled with long duration, can't be easily reverted. Test with short duration first:
```bash
SECURE_HSTS_SECONDS=300  # 5 minutes for testing
```

---

### Cookie Security

```bash
# Production settings
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SESSION_COOKIE_SAMESITE=Strict
```

**Development (HTTP only):**
```bash
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
```

---

### Admin Authentication

```bash
# Restricted admin backend (environment-based authentication)
ALLOWED_ADMIN_USERNAME=admin
ALLOWED_ADMIN_EMAIL=admin@example.com

# Generate password hash:
# python -c "from django.contrib.auth.hashers import make_password; print(make_password('your-password'))"
ALLOWED_ADMIN_PASSWORD_HASH=pbkdf2_sha256$600000$xxxxx...
```

---

## CDN & External Services

### CDN Configuration

```bash
# Enable CDN
CDN_ENABLED=True
CDN_DOMAIN=cdn.example.com

# When CDN_ENABLED=True, static files will be served from:
# https://cdn.example.com/static/
```

---

### External Service URLs

**All external service URLs are configurable via environment variables:**

```bash
# Google Services
GOOGLE_FONTS_URL=https://fonts.googleapis.com
GOOGLE_FONTS_STATIC_URL=https://fonts.gstatic.com
GOOGLE_ANALYTICS_URL=https://www.google-analytics.com

# CDN Services
CDN_TAILWIND_URL=https://cdn.tailwindcss.com
CDN_JSDELIVR_URL=https://cdn.jsdelivr.net
CDN_UNPKG_URL=https://unpkg.com
CDN_CLOUDFLARE_URL=https://cdnjs.cloudflare.com

# Social Media URLs (customize for your brand)
SOCIAL_GITHUB_URL=https://github.com/yourusername
SOCIAL_LINKEDIN_URL=https://linkedin.com/in/yourprofile
SOCIAL_TWITTER_URL=https://twitter.com/yourhandle
SOCIAL_CAL_URL=https://cal.com/yourusername
```

**Usage in Code:**
```python
from django.conf import settings

# Access external service URLs
github_url = settings.EXTERNAL_SERVICES['social_github']
fonts_url = settings.EXTERNAL_SERVICES['google_fonts']
```

---

## API Keys & Secrets

### PageSpeed API Key

```bash
# Google PageSpeed Insights API (optional)
PAGESPEED_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

**Obtain Key:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable PageSpeed Insights API
3. Create credentials → API Key

---

### VAPID Keys (Push Notifications)

```bash
VAPID_PUBLIC_KEY=BHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
VAPID_PRIVATE_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
VAPID_ADMIN_EMAIL=admin@example.com
```

**Generate Keys:**
```bash
python manage.py generate_vapid_keys
```

---

### MeiliSearch Configuration

```bash
MEILI_HOST=http://localhost:7700
MEILI_MASTER_KEY=your-master-key-here
MEILI_INDEX_NAME=portfolio_search
```

---

## Monitoring & Logging

### Sentry Error Tracking

```bash
# Sentry DSN (optional)
SENTRY_DSN=https://xxxxx@o123456.ingest.sentry.io/7890123
SENTRY_TRACES_SAMPLE_RATE=0.1
ENVIRONMENT=production
```

**Setup:**
1. Create account at [sentry.io](https://sentry.io)
2. Create new project
3. Copy DSN from project settings

---

### Logging Configuration

```bash
# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO
DJANGO_LOG_LEVEL=INFO
```

---

## Feature Flags

```bash
# Enable/disable application features
ENABLE_SEARCH=True
ENABLE_BLOG=True
ENABLE_PORTFOLIO=True
ENABLE_TOOLS=True
ENABLE_CONTACT=True
ENABLE_CHAT=True

# PWA Features
PWA_ENABLED=True
PUSH_NOTIFICATIONS=True
SERVICE_WORKER_ENABLED=True

# Performance Features
PERFORMANCE_MONITORING=True
ANALYTICS_ENABLED=True
LAZY_LOADING_ENABLED=True

# Development Tools
ENABLE_DEBUG_TOOLBAR=False
```

---

## Environment-Specific Examples

### Development `.env`

```bash
# Core
SECRET_KEY=dev-secret-key-not-for-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_SETTINGS_MODULE=project.settings.development

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Cache (optional)
REDIS_URL=redis://localhost:6379/0

# Email (console)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Security (relaxed for HTTP)
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False

# Features
ENABLE_DEBUG_TOOLBAR=True
```

---

### Production `.env`

```bash
# Core (REQUIRED)
SECRET_KEY=<generate-strong-key-here>
DEBUG=False
ALLOWED_HOSTS=example.com,.example.com
DJANGO_SETTINGS_MODULE=project.settings.production

# Database (REQUIRED)
DATABASE_URL=postgresql://user:password@host:5432/dbname
DB_CONN_MAX_AGE=600

# Cache (REQUIRED for production)
REDIS_URL=redis://:password@redis-host:6379/0

# Email (REQUIRED for contact forms)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=SG.xxxxx
DEFAULT_FROM_EMAIL=noreply@example.com

# Security (REQUIRED)
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# CDN (optional)
CDN_ENABLED=True
CDN_DOMAIN=cdn.example.com

# Monitoring (recommended)
SENTRY_DSN=https://xxxxx@sentry.io/123456
LOG_LEVEL=INFO

# Social URLs (customize)
SOCIAL_GITHUB_URL=https://github.com/yourusername
SOCIAL_LINKEDIN_URL=https://linkedin.com/in/yourprofile
```

---

### Staging `.env`

```bash
# Same as production, but with:
ENVIRONMENT=staging
DEBUG=False
ALLOWED_HOSTS=staging.example.com
DATABASE_URL=postgresql://staging_user:pass@host/staging_db
SENTRY_DSN=https://staging-key@sentry.io/staging-project

# Staging-specific flags
STAGING_BANNER=True
ENABLE_TEST_DATA=True
```

---

## Security Best Practices

### ✅ DO:
- Use strong, unique SECRET_KEY for each environment
- Store secrets in secure vault (AWS Secrets Manager, Vault, etc.)
- Use environment variables, never commit to git
- Rotate credentials regularly
- Enable HTTPS and HSTS in production
- Use secure cookies (`Secure`, `HttpOnly`, `SameSite`)
- Set specific ALLOWED_HOSTS (never use `*` in production)

### ❌ DON'T:
- Commit `.env` files to version control
- Share production credentials
- Use weak passwords
- Use same SECRET_KEY across environments
- Run with DEBUG=True in production
- Use `ALLOWED_HOSTS=*` in production

---

## Troubleshooting

### Issue: `SECRET_KEY` not set
**Error:** `ImproperlyConfigured: The SECRET_KEY setting must not be empty`
**Solution:** Generate and set SECRET_KEY in `.env`

### Issue: `ALLOWED_HOSTS` validation failed
**Error:** `DisallowedHost at / Invalid HTTP_HOST header`
**Solution:** Add your domain to ALLOWED_HOSTS

### Issue: Database connection failed
**Error:** `OperationalError: could not connect to server`
**Solution:** Check DATABASE_URL format and credentials

### Issue: Redis connection failed
**Error:** `ConnectionError: Error connecting to Redis`
**Solution:** Verify REDIS_URL and ensure Redis is running

---

## Secret Rotation Procedures

See [Secret Rotation Documentation](../security/secret-rotation.md) for:
- SECRET_KEY rotation
- Database password rotation
- API key rotation
- SSL certificate renewal

---

## References

- [Django Settings Documentation](https://docs.djangoproject.com/en/5.1/ref/settings/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/)
- [12-Factor App Methodology](https://12factor.net/)
- [OWASP Configuration Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Django_Security_Cheat_Sheet.html)

---

**Document Maintenance:**
- Review quarterly
- Update when adding new environment variables
- Keep examples current with latest Django version
