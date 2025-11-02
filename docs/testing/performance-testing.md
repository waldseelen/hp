# Performance Testing Guide

**Document Version:** 1.0
**Last Updated:** January 2025
**Tools:** Lighthouse CI, Locust

---

## Table of Contents

1. [Overview](#overview)
2. [Lighthouse Performance Testing](#lighthouse-performance-testing)
3. [Load Testing with Locust](#load-testing-with-locust)
4. [Performance Targets](#performance-targets)
5. [Monitoring & Metrics](#monitoring--metrics)
6. [Optimization Tips](#optimization-tips)
7. [Troubleshooting](#troubleshooting)

---

## Overview

Performance testing ensures our application delivers fast, reliable experiences under various load conditions.

### Performance Testing Types

1. **Lighthouse Audits**: Page speed, accessibility, SEO, best practices
2. **Load Testing**: Application behavior under concurrent users
3. **Stress Testing**: System limits and breaking points
4. **Endurance Testing**: Stability over extended periods

### Performance Targets

| Metric | Target | Critical Threshold |
|--------|--------|-------------------|
| **Lighthouse Performance** | ≥90 | ≥80 |
| **Lighthouse Accessibility** | ≥95 | ≥90 |
| **p95 Response Time** | <200ms | <500ms |
| **Error Rate** | <1% | <5% |
| **Throughput** | >100 req/s | >50 req/s |
| **Success Rate** | >99% | >95% |

---

## Lighthouse Performance Testing

### Setup

```bash
# Install Lighthouse CI
npm install -g @lhci/cli

# Or use existing installation
npm install
```

### Configuration

Lighthouse is configured in `lighthouserc.js`:

```javascript
module.exports = {
  ci: {
    collect: {
      url: [
        'http://localhost:8000/',
        'http://localhost:8000/contact/',
        'http://localhost:8000/blog/',
      ],
      numberOfRuns: 3,  // Average of 3 runs
      settings: {
        preset: 'desktop',
        onlyCategories: ['performance', 'accessibility', 'best-practices', 'seo'],
      },
    },
    assert: {
      assertions: {
        'categories:performance': ['warn', { minScore: 0.90 }],
        'categories:accessibility': ['error', { minScore: 0.95 }],
        // ... more assertions
      },
    },
  },
};
```

### Running Lighthouse Tests

#### Local Testing

```bash
# Start Django server
python manage.py runserver

# Run Lighthouse (in another terminal)
npm run lighthouse

# Or with specific URL
lhci autorun --url=http://localhost:8000/
```

#### CI Testing

```bash
# GitHub Actions automatically runs Lighthouse
# See .github/workflows/testing.yml

# Manual CI run
lhci autorun
```

### Understanding Lighthouse Scores

#### Performance Score (Target: ≥90)

Key metrics:
- **First Contentful Paint (FCP)**: <2000ms
- **Largest Contentful Paint (LCP)**: <2500ms
- **Cumulative Layout Shift (CLS)**: <0.1
- **Total Blocking Time (TBT)**: <300ms
- **Speed Index**: <3000ms

#### Accessibility Score (Target: ≥95)

Checks:
- Color contrast (WCAG AA)
- ARIA attributes
- Form labels
- Alt text for images
- Heading hierarchy
- Keyboard navigation

#### Best Practices Score (Target: ≥90)

Checks:
- HTTPS usage
- Console errors
- Image aspect ratios
- Deprecated APIs
- Security vulnerabilities

#### SEO Score (Target: ≥90)

Checks:
- Meta tags
- Mobile-friendly
- Structured data
- Canonical URLs
- Crawlability

### Lighthouse Reports

```bash
# View HTML report
npx playwright test --reporter=html
npx playwright show-report

# JSON report for programmatic access
lhci autorun --config=lighthouserc.js

# CI/CD integration
# Reports stored in .lighthouseci/lighthouse-ci.db
```

### Performance Budgets

Set in `lighthouserc.js`:

```javascript
assertions: {
  'first-contentful-paint': ['warn', { maxNumericValue: 2000 }],
  'largest-contentful-paint': ['warn', { maxNumericValue: 2500 }],
  'cumulative-layout-shift': ['warn', { maxNumericValue: 0.1 }],
  'total-blocking-time': ['warn', { maxNumericValue: 300 }],
  'speed-index': ['warn', { maxNumericValue: 3000 }],
}
```

---

## Load Testing with Locust

### Setup

```bash
# Install Locust
pip install locust

# Verify installation
locust --version
```

### Test Configuration

Load tests are defined in `tests/load/locustfile.py`:

```python
from locust import HttpUser, task, between

class HomepageUser(HttpUser):
    wait_time = between(1, 3)
    weight = 40  # 40% of users

    @task(10)
    def load_homepage(self):
        self.client.get("/")
```

### Running Load Tests

#### Web UI Mode (Recommended)

```bash
# Start Locust web interface
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Open browser
# Navigate to http://localhost:8089

# Configure test:
# - Number of users: 100
# - Spawn rate: 10 users/second
# - Host: http://localhost:8000
```

#### Headless Mode (CI/CD)

```bash
# Baseline test (10 users, 1 minute)
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --users 10 \
  --spawn-rate 2 \
  --run-time 1m \
  --headless

# Moderate load (50 users, 5 minutes)
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --users 50 \
  --spawn-rate 10 \
  --run-time 5m \
  --headless

# High load (100 users, 10 minutes)
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --users 100 \
  --spawn-rate 20 \
  --run-time 10m \
  --headless

# Stress test (200 users, 15 minutes)
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --users 200 \
  --spawn-rate 30 \
  --run-time 15m \
  --headless
```

#### Advanced Scenarios

```bash
# Spike test (0 → 100 → 0 users)
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --users 100 \
  --spawn-rate 100 \
  --run-time 2m \
  --headless

# Endurance test (50 users, 1 hour)
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --users 50 \
  --spawn-rate 10 \
  --run-time 1h \
  --headless

# Custom CSV report
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --users 100 \
  --spawn-rate 20 \
  --run-time 10m \
  --headless \
  --csv=results/load-test
```

### Load Test Scenarios

#### 1. Homepage Load (100 concurrent users)

Tests homepage performance under heavy traffic.

**Expected Results:**
- Response time p50: 50-100ms
- Response time p95: 100-200ms
- Error rate: <1%
- Throughput: 100-200 req/s

#### 2. Blog Browsing (50 concurrent users)

Tests blog list and detail page performance.

**Expected Results:**
- List page p95: 150-250ms
- Detail page p95: 100-200ms
- Error rate: <1%

#### 3. API Endpoints (30 concurrent users)

Tests REST API performance.

**Expected Results:**
- Response time p95: 50-150ms
- Error rate: <0.5%
- Throughput: 50-100 req/s

#### 4. Contact Form (20 concurrent users)

Tests form submission under load.

**Expected Results:**
- Response time p95: 200-400ms
- Error rate: <2%
- Successful submissions: >98%

### Interpreting Locust Results

#### Requests Tab

- **# Requests**: Total request count
- **# Fails**: Failed requests
- **Median**: 50th percentile response time
- **95%ile**: 95th percentile response time
- **Average**: Mean response time
- **Min/Max**: Range of response times
- **RPS**: Requests per second
- **Failures/s**: Errors per second

#### Charts Tab

- **Total Requests per Second**: Throughput over time
- **Response Times**: Latency percentiles
- **Number of Users**: User ramp-up/down
- **Failures per Second**: Error rate

---

## Performance Targets

### Response Time Targets

| Page Type | p50 | p95 | p99 |
|-----------|-----|-----|-----|
| **Homepage** | <100ms | <200ms | <500ms |
| **Blog List** | <150ms | <250ms | <600ms |
| **Blog Detail** | <100ms | <200ms | <500ms |
| **Contact Form** | <200ms | <400ms | <800ms |
| **API Endpoints** | <50ms | <150ms | <300ms |
| **Static Assets** | <50ms | <100ms | <200ms |

### Load Capacity Targets

| Scenario | Concurrent Users | Duration | Success Rate |
|----------|-----------------|----------|--------------|
| **Baseline** | 10 | 1 minute | >99% |
| **Normal Load** | 50 | 5 minutes | >99% |
| **Peak Load** | 100 | 10 minutes | >98% |
| **Stress** | 200 | 15 minutes | >95% |

### Resource Utilization Targets

| Resource | Normal Load | Peak Load | Critical |
|----------|------------|-----------|----------|
| **CPU** | <50% | <80% | >90% |
| **Memory** | <60% | <85% | >95% |
| **Database Connections** | <50% | <75% | >90% |
| **Cache Hit Rate** | >80% | >70% | <50% |

---

## Monitoring & Metrics

### Django Debug Toolbar

```python
# settings/development.py
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

# Monitor:
# - SQL queries (watch for N+1)
# - Cache hits/misses
# - Template rendering time
```

### Application Performance Monitoring

```bash
# Install APM tools
pip install django-silk  # SQL query profiling
pip install django-querycount  # N+1 detection

# Or use external APM
# - New Relic
# - DataDog
# - Sentry Performance
```

### Key Metrics to Monitor

1. **Response Times**
   - p50, p95, p99 latencies
   - Per-endpoint breakdown

2. **Error Rates**
   - HTTP 4xx/5xx errors
   - Database errors
   - Cache failures

3. **Throughput**
   - Requests per second
   - Data transfer rate

4. **Resource Usage**
   - CPU utilization
   - Memory consumption
   - Disk I/O
   - Network bandwidth

5. **Database Performance**
   - Query count per request
   - Slow queries (>100ms)
   - Connection pool usage
   - Lock contention

---

## Optimization Tips

### Frontend Optimization

#### 1. Minimize HTTP Requests

```html
<!-- Combine CSS -->
<link rel="stylesheet" href="/static/css/output.css">

<!-- Combine JS -->
<script src="/static/js/bundle.min.js"></script>

<!-- Inline critical CSS -->
<style>/* Critical CSS here */</style>
```

#### 2. Optimize Images

```bash
# Use WebP format
python manage.py optimize_images

# Lazy load images
<img src="placeholder.jpg" data-src="actual.jpg" loading="lazy">

# Responsive images
<img srcset="small.jpg 480w, large.jpg 1200w" sizes="(max-width: 600px) 480px, 1200px">
```

#### 3. Enable Compression

```python
# settings.py
MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',  # Add this
    # ... other middleware
]
```

#### 4. Cache Static Assets

```nginx
# nginx.conf
location /static/ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### Backend Optimization

#### 1. Database Query Optimization

```python
# Bad: N+1 queries
for post in BlogPost.objects.all():
    print(post.author.name)  # Query per post!

# Good: Use select_related
posts = BlogPost.objects.select_related('author').all()
for post in posts:
    print(post.author.name)  # No extra queries

# Use prefetch_related for many-to-many
posts = BlogPost.objects.prefetch_related('tags').all()
```

#### 2. Implement Caching

```python
from django.core.cache import cache

# Cache expensive queries
def get_popular_posts():
    cached = cache.get('popular_posts')
    if cached:
        return cached

    posts = BlogPost.objects.order_by('-views')[:10]
    cache.set('popular_posts', posts, 3600)  # 1 hour
    return posts

# Template fragment caching
{% load cache %}
{% cache 3600 sidebar %}
    <!-- Expensive sidebar content -->
{% endcache %}
```

#### 3. Optimize Database Indexes

```python
class BlogPost(models.Model):
    title = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(unique=True, db_index=True)
    created_at = models.DateTimeField(db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
```

#### 4. Use Async Views (Django 4.1+)

```python
from django.http import JsonResponse

async def api_endpoint(request):
    import asyncio
    # Concurrent external API calls
    results = await asyncio.gather(
        fetch_data_1(),
        fetch_data_2(),
    )
    return JsonResponse({'data': results})
```

### Infrastructure Optimization

#### 1. Use CDN for Static Files

```python
# settings/production.py
STATIC_URL = 'https://cdn.example.com/static/'
MEDIA_URL = 'https://cdn.example.com/media/'
```

#### 2. Enable HTTP/2

```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    # ...
}
```

#### 3. Configure Connection Pooling

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'CONN_MAX_AGE': 600,  # Connection pooling
    }
}
```

---

## Troubleshooting

### Slow Page Load

**Symptoms:** Lighthouse Performance < 70

**Diagnosis:**
1. Check Lighthouse report for specific issues
2. Look at waterfall diagram for blocking resources
3. Analyze Total Blocking Time (TBT)

**Solutions:**
- Defer non-critical JS: `<script defer>`
- Remove unused CSS
- Optimize images
- Minimize JavaScript execution

### High Response Times

**Symptoms:** p95 > 500ms

**Diagnosis:**
```python
# Enable Django Debug Toolbar
# Check SQL queries tab

# Or use django-silk
python manage.py runserver

# Log slow queries
LOGGING = {
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
        },
    },
}
```

**Solutions:**
- Add database indexes
- Use select_related/prefetch_related
- Implement caching
- Reduce query count

### High Error Rate

**Symptoms:** >1% errors in Locust

**Diagnosis:**
```bash
# Check Django logs
tail -f logs/django.log

# Check error responses
# Locust Failures tab shows error details
```

**Solutions:**
- Fix application bugs
- Increase database connection pool
- Add rate limiting
- Scale infrastructure

### Memory Leaks

**Symptoms:** Memory usage increases over time

**Diagnosis:**
```bash
# Monitor memory with htop
htop

# Use memory profiler
pip install memory-profiler
python -m memory_profiler manage.py runserver
```

**Solutions:**
- Close database connections
- Clear cache periodically
- Fix circular references
- Use connection pooling

---

## Performance Testing Checklist

### Before Testing

- [ ] Database is migrated
- [ ] Static files are collected
- [ ] Cache is warmed up
- [ ] Test data is populated
- [ ] Monitoring is enabled

### During Testing

- [ ] Monitor CPU usage
- [ ] Monitor memory usage
- [ ] Watch for errors
- [ ] Check database connections
- [ ] Monitor cache hit rate

### After Testing

- [ ] Analyze Lighthouse reports
- [ ] Review Locust statistics
- [ ] Check for N+1 queries
- [ ] Identify bottlenecks
- [ ] Document findings
- [ ] Create optimization tasks

---

## Resources

- [Lighthouse Documentation](https://developers.google.com/web/tools/lighthouse)
- [Locust Documentation](https://docs.locust.io/)
- [Django Performance](https://docs.djangoproject.com/en/stable/topics/performance/)
- [Web.dev Performance](https://web.dev/performance/)

---

**Document Changelog:**

| Date | Version | Changes |
|------|---------|---------|
| Jan 2025 | 1.0 | Initial version - Performance testing infrastructure complete |
