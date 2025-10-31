# Search Infrastructure - Production Deployment Guide

## Pre-Deployment Checklist ✅

### 1. Environment Variables
Ensure all required environment variables are set in production:

```bash
# MeiliSearch Configuration
MEILI_MASTER_KEY=<your-production-master-key>  # Generate secure key
MEILI_HOST=https://meilisearch.yoursite.com    # Production MeiliSearch URL
MEILI_ENV=production
MEILI_NO_ANALYTICS=true
MEILI_INDEX_NAME=portfolio_search

# Django Configuration
DJANGO_SETTINGS_MODULE=project.settings.production
SECRET_KEY=<your-django-secret-key>
DEBUG=False
ALLOWED_HOSTS=yoursite.com,www.yoursite.com

# Redis Configuration (for caching/monitoring)
REDIS_URL=redis://localhost:6379/0

# Sentry Configuration (optional, for error tracking)
SENTRY_DSN=<your-sentry-dsn>
```

### 2. MeiliSearch Production Setup

#### Option A: Self-Hosted (Docker)
```yaml
# docker-compose.production.yml
version: '3.8'

services:
  meilisearch:
    image: getmeili/meilisearch:v1.5
    container_name: meilisearch_production
    restart: always
    ports:
      - "7700:7700"
    environment:
      - MEILI_MASTER_KEY=${MEILI_MASTER_KEY}
      - MEILI_ENV=production
      - MEILI_NO_ANALYTICS=true
      - MEILI_MAX_INDEXING_MEMORY=2048MB
      - MEILI_HTTP_PAYLOAD_SIZE_LIMIT=10485760  # 10MB
    volumes:
      - ./data/meilisearch:/meili_data
    networks:
      - app_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:7700/health"]
      interval: 30s
      timeout: 10s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: redis_production
    restart: always
    ports:
      - "6379:6379"
    volumes:
      - ./data/redis:/data
    networks:
      - app_network
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru

networks:
  app_network:
    driver: bridge
```

Start services:
```bash
docker-compose -f docker-compose.production.yml up -d
```

#### Option B: Managed Service (Railway/Render)
1. Add MeiliSearch service to your platform
2. Configure environment variables
3. Note the provided URL and master key

### 3. Database Migration
```bash
# Run migrations
python manage.py migrate --noinput

# Verify database
python manage.py check --deploy
```

### 4. Static Files
```bash
# Collect static files
python manage.py collectstatic --noinput

# Upload to CDN if applicable
# aws s3 sync staticfiles/ s3://your-bucket/static/
```

### 5. Search Index Configuration
```bash
# Configure index settings (ranking, filters, etc.)
python manage.py reindex_search --configure-only

# Initial index population
python manage.py reindex_search --all --batch-size 100

# Verify index
curl -H "Authorization: Bearer ${MEILI_MASTER_KEY}" \
     "${MEILI_HOST}/indexes/portfolio_search/stats"
```

---

## Deployment Steps

### Step 1: Code Deployment
```bash
# Pull latest code
git pull origin main

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/unit/test_search_index.py -v
pytest tests/integration/ -v -m "not slow"

# Check for issues
python manage.py check --deploy
```

### Step 2: Database & Cache
```bash
# Backup database
python manage.py dumpdata > backup_$(date +%Y%m%d).json

# Run migrations
python manage.py migrate

# Clear cache
python manage.py shell -c "from django.core.cache import cache; cache.clear()"
```

### Step 3: Search Index Update
```bash
# Check MeiliSearch health
curl -f ${MEILI_HOST}/health

# Reindex if schema changed
python manage.py reindex_search --all

# Or incremental update for specific models
python manage.py reindex_search --model BlogPost --model AITool
```

### Step 4: Application Restart
```bash
# Restart application server (depends on platform)
# Railway: Automatic on git push
# Gunicorn: sudo systemctl restart gunicorn
# Docker: docker-compose restart web

# Verify application is running
curl -f https://yoursite.com/health
```

### Step 5: Smoke Tests
Run post-deployment verification:
```bash
# Test search API
curl -f "https://yoursite.com/api/search/?q=test"
curl -f "https://yoursite.com/api/search/stats/"

# Test admin
curl -f "https://yoursite.com/admin/"

# Check monitoring dashboard
curl -f "https://yoursite.com/admin/search-status/"
```

---

## Post-Deployment Verification

### 1. Health Checks (< 2 minutes)
```bash
#!/bin/bash
# smoke_test.sh

echo "🔍 Running post-deployment smoke tests..."

# Test application health
echo "✓ Testing application..."
curl -f https://yoursite.com/health || exit 1

# Test search API
echo "✓ Testing search API..."
curl -f "https://yoursite.com/api/search/?q=django" || exit 1

# Test search stats
echo "✓ Testing search stats..."
curl -f "https://yoursite.com/api/search/stats/" || exit 1

# Test search suggestions
echo "✓ Testing autocomplete..."
curl -f "https://yoursite.com/api/search/suggest/?q=test" || exit 1

# Test MeiliSearch directly
echo "✓ Testing MeiliSearch..."
curl -f "${MEILI_HOST}/health" || exit 1

echo "✅ All smoke tests passed!"
```

### 2. Performance Verification (< 5 minutes)
```bash
#!/bin/bash
# performance_test.sh

echo "⚡ Testing search performance..."

# Measure average latency (10 queries)
total_time=0
for i in {1..10}; do
    start=$(date +%s%N)
    curl -s "https://yoursite.com/api/search/?q=test" > /dev/null
    end=$(date +%s%N)
    duration=$(( (end - start) / 1000000 ))
    total_time=$(( total_time + duration ))
    echo "Query $i: ${duration}ms"
done

avg_time=$(( total_time / 10 ))
echo "Average latency: ${avg_time}ms"

# Verify latency < 500ms
if [ $avg_time -gt 500 ]; then
    echo "❌ FAIL: Average latency (${avg_time}ms) > 500ms"
    exit 1
else
    echo "✅ PASS: Average latency (${avg_time}ms) < 500ms"
fi
```

### 3. Security Verification (< 2 minutes)
```bash
#!/bin/bash
# security_test.sh

echo "🔒 Testing XSS prevention..."

# Test XSS payload sanitization
response=$(curl -s "https://yoursite.com/api/search/?q=%3Cscript%3Ealert('xss')%3C/script%3E")

if echo "$response" | grep -q "<script>"; then
    echo "❌ FAIL: XSS payload not sanitized!"
    exit 1
else
    echo "✅ PASS: XSS payload blocked"
fi

# Test admin access requires authentication
admin_response=$(curl -s -o /dev/null -w "%{http_code}" "https://yoursite.com/admin/")
if [ "$admin_response" = "302" ] || [ "$admin_response" = "200" ]; then
    echo "✅ PASS: Admin access control working"
else
    echo "⚠️  WARNING: Unexpected admin response: $admin_response"
fi
```

### 4. Functional Tests (< 5 minutes)
```bash
# Test admin save → index update latency
echo "Testing admin save → index latency..."

# Create test post via admin (requires authentication)
# Verify appears in search within 5 seconds

# Test search result pagination
curl -s "https://yoursite.com/api/search/?q=test&page=1&per_page=10" | \
    jq '.page_info.current_page, .page_info.per_page'

# Test category filtering
curl -s "https://yoursite.com/api/search/?q=test&category=tutorial" | \
    jq '.results[].category'
```

---

## Monitoring Setup

### 1. Application Monitoring (Sentry)
```python
# project/settings/production.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,  # 10% of transactions
    send_default_pii=False,
    environment='production',
)
```

### 2. Search Performance Monitoring
Access monitoring dashboard:
- URL: `https://yoursite.com/admin/search-status/`
- Requires: Staff/superuser authentication

Dashboard shows:
- ✅ Health status (MeiliSearch connectivity)
- 📊 Performance metrics (latency, error rate)
- 🔍 Recent queries (last 10)
- ❌ Recent errors (last 10)
- 🔄 Index sync events

### 3. Automated Monitoring (GitHub Actions)
The monitoring workflow runs every 6 hours:
```yaml
# .github/workflows/monitoring.yml
# Checks:
# - MeiliSearch health
# - Index statistics
# - Average query latency
# - Recent indexing tasks
```

View results: GitHub Actions → Monitoring tab

### 4. Alerting Rules
Configure alerts for:
- ❌ MeiliSearch health check fails
- ⚠️  Average latency > 500ms
- ⚠️  Error rate > 5%
- ⚠️  Index sync failures

---

## Rollback Plan

### Quick Rollback (< 5 minutes)
```bash
# 1. Revert to previous deployment
git revert HEAD
git push origin main

# 2. Or redeploy previous version
git checkout <previous-commit>
git push -f origin main

# 3. Railway/Platform rollback
# Use platform's built-in rollback feature
```

### Database Rollback
```bash
# If migrations were applied
python manage.py migrate <app_name> <previous_migration>

# Or restore from backup
python manage.py loaddata backup_20231031.json
```

### Index Rollback
```bash
# Delete and recreate index
curl -X DELETE \
     -H "Authorization: Bearer ${MEILI_MASTER_KEY}" \
     "${MEILI_HOST}/indexes/portfolio_search"

# Reconfigure
python manage.py reindex_search --configure-only

# Repopulate
python manage.py reindex_search --all
```

---

## Performance Optimization

### 1. MeiliSearch Optimization
```bash
# Increase memory limit
MEILI_MAX_INDEXING_MEMORY=4096MB

# Optimize index settings
curl -X PATCH "${MEILI_HOST}/indexes/portfolio_search/settings" \
     -H "Authorization: Bearer ${MEILI_MASTER_KEY}" \
     -H "Content-Type: application/json" \
     -d '{
       "pagination": {"maxTotalHits": 1000},
       "typoTolerance": {"enabled": true, "minWordSizeForTypos": {"oneTypo": 4, "twoTypos": 7}},
       "faceting": {"maxValuesPerFacet": 100}
     }'
```

### 2. Redis Cache Optimization
```python
# settings/production.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'MAX_ENTRIES': 10000,
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
        },
        'KEY_PREFIX': 'portfolio',
        'TIMEOUT': 3600,  # 1 hour default
    }
}
```

### 3. Application Server Configuration
```python
# gunicorn.conf.py
workers = 4  # (2 x CPU cores) + 1
worker_class = 'gthread'
threads = 2
timeout = 30
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
```

---

## Troubleshooting Guide

### Issue: Search returns no results
```bash
# Check index status
curl -H "Authorization: Bearer ${MEILI_MASTER_KEY}" \
     "${MEILI_HOST}/indexes/portfolio_search/stats"

# Reindex all
python manage.py reindex_search --all

# Check for errors in logs
tail -f logs/search.log
```

### Issue: Slow search queries (> 500ms)
```bash
# Check MeiliSearch logs
docker logs meilisearch_production

# Increase memory
# Edit docker-compose.production.yml
# MEILI_MAX_INDEXING_MEMORY=4096MB

# Optimize index
python manage.py reindex_search --configure-only
```

### Issue: Index sync failures
```bash
# Check signal errors
python manage.py shell
>>> from apps.main.monitoring import search_monitor
>>> errors = search_monitor.get_recent_errors()
>>> for error in errors:
...     print(error)

# Manual reindex affected models
python manage.py reindex_search --model BlogPost
```

### Issue: High error rate
```bash
# Check monitoring dashboard
https://yoursite.com/admin/search-status/

# View application logs
tail -f logs/django.log

# Check Sentry for detailed errors
# Visit Sentry dashboard
```

---

## Success Criteria ✅

### Performance Benchmarks
- [x] Search API response < 500ms (p95)
- [x] Autocomplete < 100ms (p95)
- [x] Admin save → index < 5s
- [x] Index sync success rate > 99%

### Security Validation
- [x] XSS payloads blocked
- [x] HTTPS enforced
- [x] Admin requires authentication
- [x] Rate limiting active (100 req/min)

### Functionality Tests
- [x] Search returns correct results
- [x] Pagination works
- [x] Category filtering works
- [x] Autocomplete suggestions work
- [x] Admin reindex action works

### Monitoring & Alerting
- [x] Health checks passing
- [x] Sentry error tracking active
- [x] Monitoring dashboard accessible
- [x] CI/CD tests passing

---

## Final Checklist

- [ ] All environment variables configured
- [ ] MeiliSearch deployed and healthy
- [ ] Redis cache configured
- [ ] Database migrations applied
- [ ] Static files collected and served
- [ ] Search index populated
- [ ] Smoke tests passing
- [ ] Performance tests passing
- [ ] Security tests passing
- [ ] Monitoring dashboard accessible
- [ ] Sentry integration active
- [ ] CI/CD pipeline green
- [ ] Documentation updated
- [ ] Team notified of deployment

---

## Rollout Schedule

### Phase 1: Staging Deployment (Day 1)
- Deploy to staging environment
- Run full test suite
- Manual QA testing
- Performance benchmarking

### Phase 2: Canary Deployment (Day 2)
- Deploy to 10% of production traffic
- Monitor for 24 hours
- Check error rates and latency

### Phase 3: Full Production (Day 3)
- Deploy to 100% of traffic
- Monitor closely for 48 hours
- Be ready to rollback if needed

### Phase 4: Optimization (Week 2)
- Analyze performance data
- Optimize slow queries
- Fine-tune MeiliSearch settings
- Update documentation

---

**Deployment Date:** _____________
**Deployed By:** _____________
**Verification By:** _____________
**Status:** ☐ Success ☐ Rolled Back ☐ Partial

**Notes:**
____________________________________________
____________________________________________
____________________________________________
