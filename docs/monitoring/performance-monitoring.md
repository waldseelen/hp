# Performance Monitoring & Optimization Guide

**Last Updated:** 2025-11-01
**Phase:** 21 - Performance Optimization & Monitoring
**Status:** Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Database Query Optimization](#database-query-optimization)
3. [Caching Strategy](#caching-strategy)
4. [Static Assets Optimization](#static-assets-optimization)
5. [Monitoring & Alerting](#monitoring--alerting)
6. [Performance Benchmarks](#performance-benchmarks)
7. [Load Testing](#load-testing)

---

## Overview

**Performance Goals:**
- **Page Load Time (LCP):** < 2.5s
- **First Input Delay (FID):** < 100ms
- **Cumulative Layout Shift (CLS):** < 0.1
- **Time to First Byte (TTFB):** < 600ms
- **API Response Time (p95):** < 500ms

**Monitoring Stack:**
- **Error Tracking:** Sentry (configured in production.py)
- **Health Checks:** /health/, /health/readiness/, /health/liveness/
- **APM:** Custom middleware (APMMiddleware, DatabaseQueryTrackingMiddleware)
- **Performance Metrics:** PerformanceMiddleware in apps/main/middleware.py

---

## Database Query Optimization

### Current Optimizations (Phase 19)

✅ **Query Optimization Completed:**
- `apps/blog/models.py`: PostManager with `select_related('author')`
- `apps/blog/models.py`: `get_related_posts()` with query optimization
- All manager methods use `select_related()` and `prefetch_related()`

✅ **Database Indexes:**
```python
# Post Model (apps/blog/models.py)
indexes = [
    models.Index(fields=['status', '-published_at']),
    models.Index(fields=['author', '-published_at']),
    models.Index(fields=['slug']),
]

# Tool Model (apps/tools/models.py)
indexes = [
    models.Index(fields=['category', '-created_at']),
    models.Index(fields=['is_featured', '-created_at']),
    models.Index(fields=['slug']),
]
```

### Query Optimization Patterns

#### Pattern 1: Select Related (Foreign Keys)
```python
# ❌ Bad: N+1 queries
posts = Post.objects.all()
for post in posts:
    print(post.author.name)  # Each iteration hits database

# ✅ Good: Single JOIN query
posts = Post.objects.select_related('author').all()
for post in posts:
    print(post.author.name)  # No additional queries
```

#### Pattern 2: Prefetch Related (Many-to-Many, Reverse ForeignKey)
```python
# ❌ Bad: N+1 queries
posts = Post.objects.all()
for post in posts:
    print(post.comments.count())  # N queries

# ✅ Good: 2 queries total
posts = Post.objects.prefetch_related('comments').all()
for post in posts:
    print(post.comments.count())  # No additional queries
```

#### Pattern 3: Only/Defer
```python
# ❌ Bad: Fetches all fields
posts = Post.objects.all()

# ✅ Good: Fetch only needed fields
posts = Post.objects.only('id', 'title', 'slug').all()

# ✅ Good: Exclude large fields
posts = Post.objects.defer('content').all()
```

### Query Performance Checklist

- [x] All manager methods use `select_related()` for foreign keys
- [x] Database indexes on frequently queried fields
- [x] Indexes on foreign keys (author_id, category_id, etc.)
- [x] Composite indexes for multi-field queries
- [ ] Regular query analysis with Django Debug Toolbar (development only)
- [ ] Monitor slow queries with APM (>100ms threshold)

---

## Caching Strategy

### Cache Configuration

**Development:**
```python
# Local memory cache (fast, non-persistent)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}
```

**Production:**
```python
# Redis cache (persistent, distributed)
REDIS_URL = config('REDIS_URL', default='')
if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 20,
                    'retry_on_timeout': True,
                },
                'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            },
            'KEY_PREFIX': 'portfolio',
            'TIMEOUT': 3600,  # 1 hour
        }
    }
```

### Cache Usage Patterns

#### Pattern 1: Cache Expensive Queries
```python
from django.core.cache import cache

def get_popular_posts():
    cache_key = 'popular_posts'
    posts = cache.get(cache_key)

    if posts is None:
        # Expensive query
        posts = Post.objects.annotate(
            score=Count('comments') + F('view_count')
        ).order_by('-score')[:10]

        # Cache for 1 hour
        cache.set(cache_key, posts, 3600)

    return posts
```

#### Pattern 2: Cache Template Fragments
```django
{% load cache %}

{% cache 3600 sidebar request.user.id %}
    <!-- Expensive template logic -->
    {% for post in popular_posts %}
        <li>{{ post.title }}</li>
    {% endfor %}
{% endcache %}
```

#### Pattern 3: Cache Invalidation Signals
```python
from django.db.models.signals import post_save, post_delete
from django.core.cache import cache

@receiver(post_save, sender=Post)
@receiver(post_delete, sender=Post)
def invalidate_post_cache(sender, instance, **kwargs):
    """Invalidate post-related caches when post is saved/deleted"""
    cache_keys = [
        'popular_posts',
        f'post_detail_{instance.slug}',
        f'post_list_{instance.category.slug}',
    ]
    cache.delete_many(cache_keys)
```

### Cached Properties

✅ **Already Implemented (Phase 19):**
```python
# apps/blog/models.py
class Post(models.Model):
    @cached_property
    def reading_time(self) -> int:
        """Cached reading time calculation"""
        return calculate_reading_time(self.content)

    @cached_property
    def word_count(self) -> int:
        """Cached word count"""
        return len(self.content.split())
```

### Cache Monitoring

**Redis Stats:**
```bash
# Connect to Redis
redis-cli -h localhost -p 6379

# Get cache statistics
INFO stats

# Monitor cache hits/misses
INFO stats | grep keyspace_hits
INFO stats | grep keyspace_misses

# Calculate hit rate
hit_rate = hits / (hits + misses) * 100
# Target: >80% hit rate
```

---

## Static Assets Optimization

### Current Setup

✅ **WhiteNoise Static File Serving:**
```python
# settings/base.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ✅ Enabled
    # ...
]

# Static files compression
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_MAX_AGE = 31536000  # 1 year cache
```

### Optimization Checklist

#### Static Files
- [x] WhiteNoise middleware enabled
- [x] Compressed manifest static files storage
- [x] Long cache headers (1 year)
- [x] Gzip compression enabled
- [ ] Brotli compression (optional upgrade)
- [ ] CDN integration (configured but optional)

#### CSS Optimization
```bash
# Minified CSS files already present
static/css/*.min.css
static/css/*.min.css.map

# Verify minification
ls static/css/*.min.css | wc -l
```

#### JavaScript Optimization
```bash
# Minified JS files already present
static/js/*.min.js
static/js/*.min.js.map

# Service Worker optimization
static/js/sw.js  # Already optimized
```

#### Image Optimization
```python
# Image optimization settings (base.py)
IMAGE_OPTIMIZATION = {
    'ENABLED': True,
    'WEBP_QUALITY': 80,
    'AVIF_QUALITY': 75,
    'JPEG_QUALITY': 85,
    'PNG_QUALITY': 90,
    'MAX_WIDTH': 2000,
    'MAX_HEIGHT': 2000,
}
```

**Image Optimization Tools:**
```bash
# Install Pillow (already in requirements.txt)
pip install Pillow

# Convert images to WebP
python manage.py convert_to_webp media/

# Compress existing images
python manage.py optimize_images media/
```

### CDN Configuration

**Setup (Optional but Recommended):**
```bash
# Environment variables
CDN_ENABLED=True
CDN_DOMAIN=cdn.example.com

# Static files will be served from:
# https://cdn.example.com/static/
```

**CloudFlare CDN (Free Tier):**
1. Add domain to CloudFlare
2. Enable "Auto Minify" for HTML/CSS/JS
3. Enable "Brotli" compression
4. Set cache rules:
   - `/static/*`: Cache for 1 year
   - `/media/*`: Cache for 1 month
   - `*.css`, `*.js`: Cache for 1 year

---

## Monitoring & Alerting

### Health Check Endpoints

✅ **Already Implemented:**
```bash
# Basic health check
GET /health/
# Response: {"status": "healthy", "timestamp": "..."}

# Kubernetes readiness probe
GET /health/readiness/
# Checks: Database, Redis, File system

# Kubernetes liveness probe
GET /health/liveness/
# Checks: Basic application health
```

**Usage in Docker/Kubernetes:**
```yaml
# docker-compose.yml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
  interval: 30s
  timeout: 10s
  retries: 3

# kubernetes.yml
livenessProbe:
  httpGet:
    path: /health/liveness/
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/readiness/
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
```

### Sentry Error Tracking

✅ **Already Configured (production.py):**
```python
SENTRY_DSN = config('SENTRY_DSN', default='')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,  # 10% of transactions
        send_default_pii=False,
    )
```

**Sentry Setup:**
1. Create account at [sentry.io](https://sentry.io)
2. Create new Django project
3. Copy DSN from project settings
4. Add to `.env`: `SENTRY_DSN=https://xxxxx@sentry.io/123456`

**Sentry Features:**
- ✅ Error tracking with stack traces
- ✅ Performance monitoring (10% sampling)
- ✅ Release tracking (optional)
- ✅ User context (if authenticated)
- ✅ Breadcrumbs (request history)

### APM (Application Performance Monitoring)

✅ **Custom APM Middleware (Already Implemented):**
```python
# apps/main/middleware.py
- APMMiddleware: Transaction tracking
- DatabaseQueryTrackingMiddleware: Slow query detection
- PerformanceMiddleware: Request timing
```

**APM Metrics Collected:**
- Request duration (total time)
- Database query count
- Database query time
- Cache hit rate
- Memory usage
- CPU usage

**Slow Query Threshold:**
```python
# settings/base.py
PERFORMANCE_BUDGETS = {
    'SLOW_TRANSACTION_THRESHOLD': 2.0,  # 2 seconds
    'VERY_SLOW_THRESHOLD': 5.0,  # 5 seconds
    'DATABASE_QUERY_THRESHOLD': 0.1,  # 100ms
}
```

### Uptime Monitoring

**Recommended Services:**
1. **UptimeRobot** (Free, 5-minute checks)
   - Monitor: https://example.com/health/
   - Alert: Email, Slack, SMS

2. **Pingdom** (Free tier available)
   - Real user monitoring (RUM)
   - Performance testing from multiple locations

3. **StatusCake** (Free tier)
   - Page speed monitoring
   - SSL certificate monitoring

**Setup Example (UptimeRobot):**
```
Monitor Type: HTTP(s)
URL: https://example.com/health/
Interval: 5 minutes
Alert Contacts: your-email@example.com
```

---

## Performance Benchmarks

### Baseline Metrics (Target)

| Metric | Target | Critical |
|--------|--------|----------|
| **LCP (Largest Contentful Paint)** | < 2.5s | < 4.0s |
| **FID (First Input Delay)** | < 100ms | < 300ms |
| **CLS (Cumulative Layout Shift)** | < 0.1 | < 0.25 |
| **TTFB (Time to First Byte)** | < 600ms | < 1800ms |
| **Total Page Size** | < 1MB | < 3MB |
| **API Response Time (p95)** | < 500ms | < 1000ms |
| **Database Query Time** | < 100ms | < 500ms |

### Lighthouse CI

**Installation:**
```bash
npm install -g @lhci/cli
```

**Configuration (lighthouserc.js):**
```javascript
module.exports = {
  ci: {
    collect: {
      url: ['http://localhost:8000/', 'http://localhost:8000/blog/'],
      numberOfRuns: 3,
    },
    assert: {
      preset: 'lighthouse:recommended',
      assertions: {
        'categories:performance': ['error', {minScore: 0.9}],
        'categories:accessibility': ['error', {minScore: 0.9}],
        'categories:best-practices': ['error', {minScore: 0.9}],
        'categories:seo': ['error', {minScore: 0.9}],
      },
    },
    upload: {
      target: 'temporary-public-storage',
    },
  },
};
```

**Run Lighthouse:**
```bash
# Start Django server
python manage.py runserver

# Run Lighthouse CI
lhci autorun

# View report
lhci open
```

---

## Load Testing

### Apache Bench (Quick Test)

```bash
# 1000 requests, 10 concurrent
ab -n 1000 -c 10 http://localhost:8000/

# With keep-alive
ab -n 1000 -c 10 -k http://localhost:8000/

# POST request
ab -n 100 -c 10 -p data.json -T application/json http://localhost:8000/api/
```

### Locust (Advanced Load Testing)

**Installation:**
```bash
pip install locust
```

**Load Test Script (locustfile.py):**
```python
from locust import HttpUser, task, between

class PortfolioUser(HttpUser):
    wait_time = between(1, 3)  # Wait 1-3s between requests

    @task(3)  # Weight: 3x more likely
    def view_homepage(self):
        self.client.get("/")

    @task(2)
    def view_blog_list(self):
        self.client.get("/blog/")

    @task(1)
    def view_blog_post(self):
        self.client.get("/blog/sample-post/")

    @task(1)
    def api_health_check(self):
        with self.client.get("/health/", catch_response=True) as response:
            if response.status_code != 200:
                response.failure("Health check failed!")
```

**Run Locust:**
```bash
# Web UI mode
locust -f locustfile.py --host=http://localhost:8000

# Headless mode (100 users, 10/sec spawn rate, 5min test)
locust -f locustfile.py --host=http://localhost:8000 \
    --headless -u 100 -r 10 --run-time 5m
```

### Load Testing Scenarios

**Scenario 1: Normal Traffic**
- Users: 50
- Spawn rate: 5/sec
- Duration: 10 minutes
- **Expected:** 0% errors, p95 < 500ms

**Scenario 2: Peak Traffic**
- Users: 200
- Spawn rate: 10/sec
- Duration: 5 minutes
- **Expected:** < 1% errors, p95 < 1000ms

**Scenario 3: Stress Test**
- Users: 500
- Spawn rate: 20/sec
- Duration: 2 minutes
- **Goal:** Find breaking point

---

## Performance Optimization Quick Wins

### 1. Enable Compression
```python
# settings/production.py
MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',  # Add this
    # ... rest of middleware
]
```

### 2. Database Connection Pooling
```python
# Already configured in production.py
DATABASES = {
    'default': {
        # ...
        'conn_max_age': 600,  # Keep connections for 10 minutes
        'conn_health_checks': True,
    }
}
```

### 3. Template Caching
```python
# settings/production.py
TEMPLATES = [{
    'OPTIONS': {
        'loaders': [
            ('django.template.loaders.cached.Loader', [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ]),
        ],
    },
}]
```

### 4. Session Storage
```python
# Use Redis for sessions (already configured)
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

---

## Monitoring Dashboard

**Recommended Tools:**

1. **Grafana + Prometheus** (Advanced)
   - Real-time metrics
   - Custom dashboards
   - Alerting rules

2. **Django Debug Toolbar** (Development Only)
   ```bash
   pip install django-debug-toolbar
   ```

3. **Simple Dashboard** (Custom)
   - View at: `/admin/performance/`
   - Metrics: Request count, avg response time, error rate
   - Already implemented in `apps/portfolio/performance.py`

---

## Checklist: Production Performance

- [x] Database indexes on frequently queried fields
- [x] Query optimization with select_related/prefetch_related
- [x] Redis caching configured
- [ ] Cache invalidation signals implemented
- [x] WhiteNoise static file serving
- [x] Static files minification
- [ ] Image optimization (WebP/AVIF conversion)
- [ ] CDN integration (optional)
- [x] Health check endpoints
- [x] Sentry error tracking
- [x] APM middleware enabled
- [ ] Uptime monitoring service
- [ ] Lighthouse CI in CI/CD
- [ ] Load testing performed
- [ ] Performance baseline documented

---

**Last Review:** 2025-11-01
**Next Review:** Monthly or after major changes
