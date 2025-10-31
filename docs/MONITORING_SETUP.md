# Search Infrastructure - Monitoring Setup Guide

## Overview

The search monitoring system provides real-time visibility into search performance, error tracking, and index health. Built with Django, Redis, and optional Sentry integration.

---

## Architecture

### Components
- **SearchMonitor** (`apps/main/monitoring.py`): Core monitoring class
- **Admin Dashboard** (`templates/admin/search_status.html`): Real-time UI
- **Cache Backend**: Redis (metrics storage, 1-hour TTL)
- **Error Tracking**: Sentry SDK (optional)

### Data Flow
```
Search Request → SearchMonitor.track_query() → Cache Metrics
                                             ↓
                                      Admin Dashboard (Auto-refresh 30s)
                                             ↓
                                      Performance Analysis
```

---

## Installation

### 1. Install Dependencies
```bash
pip install redis sentry-sdk  # Core dependencies
pip install django-redis       # Django cache backend
```

### 2. Configure Redis Cache
Add to `project/settings/base.py`:

```python
# Redis Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'CONNECTION_POOL_KWARGS': {'max_connections': 50},
            'IGNORE_EXCEPTIONS': True,  # Graceful degradation
        },
        'KEY_PREFIX': 'portfolio',
        'TIMEOUT': 3600,  # 1 hour default
    }
}
```

### 3. Configure Sentry (Optional but Recommended)
Add to `project/settings/production.py`:

```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

if os.environ.get('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=os.environ['SENTRY_DSN'],
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,  # 10% of transactions
        send_default_pii=False,
        environment=os.environ.get('DJANGO_ENV', 'production'),
        release=os.environ.get('GIT_COMMIT_SHA', 'unknown'),
    )
```

---

## Usage

### 1. Track Search Queries

**Automatic Tracking (Already Integrated)**
Search queries are automatically tracked in:
- `apps/main/views/search_views.py` (search_api, search_suggest)
- Django signals track index sync operations

**Manual Tracking**
```python
from apps.main.monitoring import search_monitor

# Track a search query
with search_monitor.track_query(query="django tutorial", user_id=request.user.id):
    # Your search logic here
    results = search_index_manager.index.search(query)
```

### 2. Log Index Sync Operations

**Automatic Logging (Already Integrated)**
Index operations are logged via Django signals:
- Model save → `sync_to_search_index()` → `search_monitor.log_index_sync()`
- Model delete → `remove_from_search_index()` → `search_monitor.log_index_sync()`

**Manual Logging**
```python
import time

start = time.time()
try:
    search_index_manager.index_document('BlogPost', document)
    duration_ms = (time.time() - start) * 1000

    search_monitor.log_index_sync(
        model_name='BlogPost',
        operation='index',
        success=True,
        duration_ms=duration_ms,
        document_count=1,
        error=None
    )
except Exception as e:
    duration_ms = (time.time() - start) * 1000
    search_monitor.log_index_sync(
        model_name='BlogPost',
        operation='index',
        success=False,
        duration_ms=duration_ms,
        document_count=0,
        error=str(e)
    )
```

### 3. Access Admin Dashboard

**URL:** `/admin/search-status/`
**Authentication:** Staff/superuser required

**Features:**
- ✅ MeiliSearch health status
- 📊 Performance metrics (latency, throughput, error rate)
- 🔍 Recent queries (last 10, color-coded by latency)
- ❌ Recent errors (last 10 if any)
- 🔄 Index sync events timeline
- 🔧 Management actions (reindex, refresh)
- ⏱️ Auto-refresh every 30 seconds

---

## Dashboard Guide

### Health Status Indicators

| Color | Status | Meaning |
|-------|--------|---------|
| 🟢 Green | Healthy | All systems operational |
| 🟡 Yellow | Warning | Latency > 100ms or error rate > 1% |
| 🔴 Red | Error | MeiliSearch unreachable or error rate > 5% |

### Performance Metrics

**Total Queries**
Count of queries in last hour (from cache)

**Average Latency**
Mean query response time in milliseconds
- ✅ < 100ms: Excellent
- ⚠️ 100-500ms: Acceptable
- ❌ > 500ms: Critical

**Error Rate**
Percentage of failed queries
- ✅ < 1%: Healthy
- ⚠️ 1-5%: Warning
- ❌ > 5%: Critical

**Max Latency**
Slowest query in monitoring window

### Recent Queries Log

Color-coded entries:
- 🟢 Green: < 100ms (fast)
- 🟡 Yellow: 100-500ms (acceptable)
- 🔴 Red: > 500ms (slow)

Shows: query text, latency, timestamp, user ID

### Recent Errors Log

Shows last 10 errors with:
- Error message
- Timestamp
- Query that failed
- User ID (if available)

### Sync Events Timeline

Logs index sync operations:
- Model type (BlogPost, AITool, etc.)
- Operation (index/delete)
- Success/failure status
- Duration
- Timestamp

---

## Monitoring API Endpoints

### 1. Dashboard Data (HTML)
```http
GET /admin/search-status/
Authorization: Session (staff required)
```

Returns rendered HTML dashboard.

### 2. Metrics API (JSON)
```http
GET /admin/search-metrics-api/
Authorization: Session (staff required)
```

Response:
```json
{
  "health": {
    "is_healthy": true,
    "status": "healthy",
    "message": "All systems operational"
  },
  "metrics": {
    "total_queries": 1234,
    "avg_latency": 45.67,
    "error_rate": 0.5,
    "max_latency": 234.56
  },
  "recent_queries": [...],
  "recent_errors": [...],
  "sync_events": [...]
}
```

### 3. Performance Chart Data
```http
GET /admin/search-performance/
Authorization: Session (staff required)
```

Returns time-series data for charting (cached 5 min).

---

## Alert Thresholds

### Performance Alerts

**Latency Warning**
- Threshold: 100ms average
- Action: Review slow queries
- Investigation: Check MeiliSearch logs, database queries

**Latency Critical**
- Threshold: 500ms average
- Action: Immediate investigation
- Investigation: Check server resources, network latency, index size

**Error Rate Warning**
- Threshold: 1% of queries failing
- Action: Review error logs
- Investigation: Check MeiliSearch connectivity, query syntax

**Error Rate Critical**
- Threshold: 5% of queries failing
- Action: Emergency response
- Investigation: Check MeiliSearch health, index corruption, network issues

### Index Sync Alerts

**Sync Failure**
- Threshold: Any failed sync operation
- Action: Log review
- Investigation: Model data validity, index schema mismatch

**Sync Latency**
- Threshold: > 5 seconds
- Action: Performance review
- Investigation: Document size, network latency, MeiliSearch load

---

## Common Issues & Solutions

### Issue: Dashboard shows "Unhealthy" status

**Symptoms:**
- Red health indicator
- "MeiliSearch unavailable" message

**Diagnosis:**
```bash
# Check MeiliSearch status
curl -f ${MEILI_HOST}/health

# Check container/service
docker ps | grep meilisearch
# or
railway logs --service meilisearch
```

**Solutions:**
1. Verify MeiliSearch is running
2. Check `MEILI_HOST` environment variable
3. Verify `MEILI_MASTER_KEY` is correct
4. Check network connectivity
5. Review MeiliSearch logs for errors

---

### Issue: High latency (> 500ms)

**Symptoms:**
- Yellow/red query entries
- Slow search responses
- User complaints

**Diagnosis:**
```python
# Check index size
python manage.py shell
>>> from apps.main.search_index import search_index_manager
>>> stats = search_index_manager.get_index_stats()
>>> print(stats['numberOfDocuments'])
```

**Solutions:**
1. **Index too large:** Consider pagination or splitting indices
2. **Unoptimized queries:** Review search filters and sorting
3. **Resource constraints:** Increase MeiliSearch memory (`MEILI_MAX_INDEXING_MEMORY`)
4. **Network latency:** Move MeiliSearch closer to application server
5. **Typo tolerance:** Reduce typo tolerance settings for faster searches

---

### Issue: High error rate (> 5%)

**Symptoms:**
- Red error rate metric
- Many entries in "Recent Errors"

**Diagnosis:**
```python
# Check recent errors
from apps.main.monitoring import search_monitor
errors = search_monitor.get_recent_errors()
for error in errors:
    print(f"{error['timestamp']}: {error['message']}")
```

**Common Causes:**
1. **Invalid queries:** XSS prevention blocking legitimate queries
2. **Index schema mismatch:** Model fields don't match index schema
3. **Network issues:** Intermittent connectivity to MeiliSearch
4. **Rate limiting:** Too many requests hitting throttle limits

**Solutions:**
1. Review error messages for patterns
2. Validate index schema: `python manage.py reindex_search --configure-only`
3. Adjust XSS sanitization rules if too strict
4. Increase rate limits if legitimate traffic
5. Check MeiliSearch logs: `docker logs meilisearch`

---

### Issue: Metrics not updating

**Symptoms:**
- Dashboard shows old data
- "Last updated" timestamp not changing

**Diagnosis:**
```bash
# Check Redis connectivity
redis-cli ping
# Response: PONG

# Check cache keys
redis-cli keys "portfolio:search:*"
```

**Solutions:**
1. Verify Redis is running and accessible
2. Check `REDIS_URL` environment variable
3. Clear cache: `python manage.py shell -c "from django.core.cache import cache; cache.clear()"`
4. Restart application to reinitialize cache connection
5. Check Redis memory: `redis-cli info memory`

---

### Issue: Sync events not appearing

**Symptoms:**
- Save model in admin, no sync event logged
- "Sync Events" section empty

**Diagnosis:**
```python
# Test signal manually
from apps.main.models import BlogPost
from apps.main.signals import sync_to_search_index

post = BlogPost.objects.first()
sync_to_search_index(sender=BlogPost, instance=post, created=False)
```

**Solutions:**
1. Verify signals are connected (check `apps.py` `ready()` method)
2. Check `search_monitor.log_index_sync()` is called in signals
3. Review signal error logs: `tail -f logs/django.log`
4. Manually trigger reindex: `/admin/search-status/` → "Trigger Reindex"

---

## Performance Optimization

### 1. Cache Configuration

**Increase Cache TTL for Stable Data**
```python
# In monitoring.py
CACHE_TIMEOUT = 3600  # 1 hour for metrics
HEALTH_CHECK_CACHE = 300  # 5 minutes for health
```

**Use Connection Pooling**
```python
# In settings.py
CACHES['default']['OPTIONS']['CONNECTION_POOL_KWARGS'] = {
    'max_connections': 100,  # Increase for high traffic
    'retry_on_timeout': True,
}
```

### 2. MeiliSearch Optimization

**Adjust Memory Limits**
```bash
# docker-compose.yml
MEILI_MAX_INDEXING_MEMORY=4096MB  # Default: 2048MB
```

**Optimize Index Settings**
```python
# Reduce typo tolerance for speed
search_index_manager.index.update_settings({
    'typoTolerance': {
        'enabled': True,
        'minWordSizeForTypos': {'oneTypo': 5, 'twoTypos': 9}
    }
})
```

### 3. Query Optimization

**Limit Attributes to Search**
```python
# Only search in relevant fields
search_params['attributesToSearchOn'] = ['title', 'tags']  # Exclude 'content'
```

**Reduce Highlighting Overhead**
```python
# Disable highlights for API-only queries
if not request.GET.get('highlight'):
    search_params.pop('attributesToHighlight', None)
```

---

## Maintenance Tasks

### Daily
- [ ] Review dashboard for anomalies
- [ ] Check error rate < 1%
- [ ] Verify average latency < 100ms

### Weekly
- [ ] Review slow queries (> 500ms)
- [ ] Analyze search patterns
- [ ] Check index size growth
- [ ] Review sync event failures

### Monthly
- [ ] Analyze search metrics trends
- [ ] Optimize slow query patterns
- [ ] Review and adjust thresholds
- [ ] Update documentation with learnings

### Quarterly
- [ ] Full performance audit
- [ ] Index schema review
- [ ] Redis cache optimization
- [ ] MeiliSearch version update
- [ ] Security review

---

## Monitoring Checklist

### Initial Setup
- [ ] Redis installed and running
- [ ] Sentry DSN configured (optional)
- [ ] Environment variables set
- [ ] Admin user created
- [ ] Dashboard accessible at `/admin/search-status/`

### Verification
- [ ] Perform test search → Check recent queries list
- [ ] Save model in admin → Check sync events
- [ ] Delete model → Check sync events
- [ ] Simulate error → Check recent errors
- [ ] Wait 30s → Verify auto-refresh works

### Production Readiness
- [ ] Health checks passing
- [ ] Metrics collecting correctly
- [ ] Errors logging to Sentry
- [ ] Dashboard accessible to staff
- [ ] Alert thresholds configured
- [ ] Documentation reviewed

---

## Advanced Configuration

### Custom Thresholds

Edit `apps/main/monitoring.py`:

```python
class SearchMonitor:
    # Adjust thresholds
    LATENCY_WARNING_MS = 150  # Default: 100
    LATENCY_ERROR_MS = 600    # Default: 500
    ERROR_RATE_WARNING = 0.02 # Default: 0.01 (1%)
    ERROR_RATE_ERROR = 0.10   # Default: 0.05 (5%)
```

### Custom Cache Keys

```python
# Add custom metric
def track_custom_metric(self, metric_name, value):
    cache_key = f'search:custom:{metric_name}'
    cache.set(cache_key, value, timeout=3600)
```

### Webhook Notifications

```python
# In monitoring.py, add to log_error()
def log_error(self, error_message, query=None, user_id=None):
    # ... existing code ...

    # Send webhook for critical errors
    if self._is_critical_error(error_message):
        self._send_alert_webhook({
            'level': 'critical',
            'message': error_message,
            'query': query,
            'timestamp': timezone.now().isoformat()
        })
```

---

## Resources

- **MeiliSearch Docs:** https://docs.meilisearch.com
- **Redis Docs:** https://redis.io/docs
- **Sentry Docs:** https://docs.sentry.io
- **Django Cache:** https://docs.djangoproject.com/en/stable/topics/cache/

---

**Last Updated:** 2024
**Maintained By:** Development Team
**Support:** monitoring@yoursite.com
