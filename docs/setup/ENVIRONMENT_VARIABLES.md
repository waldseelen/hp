# Environment Variables Documentation

This document describes all environment variables used in the portfolio project and their purposes.

## Required Environment Variables

### Core Django Settings

| Variable | Default | Description | Required | Example |
|----------|---------|-------------|----------|---------|
| `SECRET_KEY` | `your-secret-key-here` | Django secret key for cryptographic signing | **Yes** | `django-insecure-secret-key-for-development` |
| `DEBUG` | `True` | Enable/disable Django debug mode | **Yes** | `False` |
| `ALLOWED_HOSTS` | `*` | Comma-separated list of allowed hostnames | **Yes** | `localhost,127.0.0.1,yourdomain.com` |
| `DJANGO_SETTINGS_MODULE` | - | Django settings module to use | **Yes** | `portfolio_site.settings.production` |

### Database Configuration

| Variable | Default | Description | Required | Example |
|----------|---------|-------------|----------|---------|
| `DATABASE_URL` | SQLite | Database connection string | No | `postgresql://user:password@localhost:5432/portfolio` |

### Cache & Session Management

| Variable | Default | Description | Required | Example |
|----------|---------|-------------|----------|---------|
| `REDIS_URL` | - | Redis connection string for caching/sessions | No | `redis://localhost:6379/0` |

### Email Configuration

| Variable | Default | Description | Required | Example |
|----------|---------|-------------|----------|---------|
| `EMAIL_HOST` | `smtp.gmail.com` | SMTP server hostname | No | `smtp.gmail.com` |
| `EMAIL_PORT` | `587` | SMTP server port | No | `587` |
| `EMAIL_USE_TLS` | `True` | Use TLS encryption | No | `True` |
| `EMAIL_HOST_USER` | - | SMTP username | No* | `your-email@gmail.com` |
| `EMAIL_HOST_PASSWORD` | - | SMTP password/app password | No* | `your-app-password` |
| `DEFAULT_FROM_EMAIL` | `noreply@example.com` | Default sender email | No | `noreply@yoursite.com` |

*Required for production email functionality

## Optional Environment Variables

### Monitoring & Observability

| Variable | Default | Description | Impact | Example |
|----------|---------|-------------|--------|---------|
| `SENTRY_DSN` | - | Sentry error tracking DSN | Error monitoring | `https://...@sentry.io/...` |
| `SENTRY_TRACES_SAMPLE_RATE` | `0.1` | Performance monitoring sample rate | Performance tracking | `0.1` |
| `ENVIRONMENT` | `development` | Environment name for monitoring | Error context | `production` |
| `APP_VERSION` | `1.0.0` | Application version for releases | Release tracking | `1.2.3` |
| `DJANGO_LOG_LEVEL` | `INFO` | Django logging level | Log verbosity | `ERROR` |

### Push Notifications

| Variable | Default | Description | Impact | Example |
|----------|---------|-------------|--------|---------|
| `VAPID_PUBLIC_KEY` | - | VAPID public key for web push | Push notifications | `BMj8f...` |
| `VAPID_PRIVATE_KEY` | - | VAPID private key for web push | Push notifications | `TKZ6H...` |
| `VAPID_ADMIN_EMAIL` | `admin@example.com` | Admin email for VAPID | Push notifications | `admin@yoursite.com` |

### Performance & Monitoring

| Variable | Default | Description | Impact | Example |
|----------|---------|-------------|--------|---------|
| `PERFORMANCE_MONITORING_ENABLED` | `True` | Enable performance monitoring | Monitoring | `True` |
| `PERFORMANCE_SAMPLE_RATE` | `0.1` | Performance sampling rate | Monitoring overhead | `0.05` |
| `TRACK_SQL_QUERIES` | `DEBUG` | Track database query performance | Debug info | `True` |
| `MAX_QUERY_TIME` | `0.1` | Maximum query time threshold (seconds) | Performance alerts | `0.05` |
| `TRACK_CACHE_HITS` | `True` | Track cache hit/miss rates | Cache optimization | `False` |

### Security Settings

| Variable | Default | Description | Impact | Example |
|----------|---------|-------------|--------|---------|
| `CSP_REPORT_ONLY` | `False` | Content Security Policy report mode | Security enforcement | `True` |
| `RATELIMIT_ENABLE` | `True` | Enable API rate limiting | API protection | `False` |

### Site Configuration

| Variable | Default | Description | Impact | Example |
|----------|---------|-------------|--------|---------|
| `SITE_NAME` | `Professional Portfolio` | Site name for metadata | SEO/branding | `John Doe Portfolio` |
| `SITE_DESCRIPTION` | `Full Stack Developer...` | Site description | SEO | `Software Engineer Portfolio` |

### Feature Flags

| Variable | Default | Description | Impact | Example |
|----------|---------|-------------|--------|---------|
| `PWA_ENABLED` | `True` | Enable Progressive Web App features | PWA functionality | `False` |
| `PUSH_NOTIFICATIONS` | `True` | Enable push notification support | Notifications | `False` |
| `PERFORMANCE_MONITORING` | `True` | Enable performance monitoring | Monitoring | `False` |
| `ANALYTICS_ENABLED` | `True` | Enable analytics tracking | Analytics | `False` |
| `SERVICE_WORKER_ENABLED` | `True` | Enable service worker | Offline support | `False` |
| `LAZY_LOADING_ENABLED` | `True` | Enable image lazy loading | Performance | `False` |

### Image Optimization

| Variable | Default | Description | Impact | Example |
|----------|---------|-------------|--------|---------|
| `IMAGE_OPTIMIZATION_ENABLED` | `True` | Enable image optimization | Performance | `False` |
| `WEBP_QUALITY` | `80` | WebP image quality (1-100) | Image quality/size | `90` |
| `AVIF_QUALITY` | `75` | AVIF image quality (1-100) | Image quality/size | `85` |
| `JPEG_QUALITY` | `85` | JPEG image quality (1-100) | Image quality/size | `90` |
| `PNG_QUALITY` | `90` | PNG image quality (1-100) | Image quality/size | `95` |
| `MAX_IMAGE_WIDTH` | `2000` | Maximum image width (pixels) | Memory usage | `1920` |
| `MAX_IMAGE_HEIGHT` | `2000` | Maximum image height (pixels) | Memory usage | `1080` |

## Environment Setup

### Development
```bash
# Copy example file
cp .env.example .env

# Edit with your values
# Minimal setup requires only SECRET_KEY and DEBUG=True
```

### Production
```bash
# Required variables for production:
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:password@host:port/database

# Recommended for production:
REDIS_URL=redis://localhost:6379/0
SENTRY_DSN=https://...@sentry.io/...
EMAIL_HOST_USER=your-email@domain.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Testing
```bash
# Test environment uses SQLite and console email backend
DJANGO_SETTINGS_MODULE=portfolio_site.settings.test
DEBUG=False
DATABASE_URL=sqlite:///test.db
```

## Configuration Validation

The application includes graceful fallbacks for missing optional variables:

- **Redis**: Falls back to local memory cache if Redis is unavailable
- **Sentry**: Disables error tracking if not configured
- **Email**: Uses console backend if SMTP credentials missing
- **Push Notifications**: Disables if VAPID keys missing

## Security Notes

1. **Never commit `.env` files** to version control
2. **Use strong, unique SECRET_KEY** in production
3. **Set DEBUG=False** in production
4. **Configure ALLOWED_HOSTS** properly
5. **Use app passwords** for email providers like Gmail
6. **Store sensitive variables** in deployment platform's secret management

## Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   - Check REDIS_URL format
   - Verify Redis server is running
   - Application will use local cache as fallback

2. **Sentry Not Working**
   - Verify SENTRY_DSN format
   - Check Sentry project settings
   - Application continues without error tracking

3. **Email Not Sending**
   - Verify SMTP credentials
   - Check EMAIL_HOST and EMAIL_PORT
   - Application falls back to console output

### Validation Commands

```bash
# Check configuration
python manage.py check

# Test database connection
python manage.py migrate --dry-run

# Verify email configuration
python manage.py sendtestemail admin@example.com
```
