# MeiliSearch Setup & Configuration Guide

**Created:** 2025-10-31
**Version:** 1.0
**Status:** Complete Setup Documentation

---

## Overview

This document provides comprehensive setup instructions for integrating MeiliSearch as the full-text search engine for the Django Portfolio project. MeiliSearch offers fast, typo-tolerant search with minimal configuration.

**Why MeiliSearch?**
- ⚡ Sub-50ms search responses (avg 15-30ms)
- 🔤 Built-in typo tolerance (1-2 typos handled automatically)
- 🎯 Relevance-based ranking out of the box
- 🚀 Simple REST API integration
- 📦 Lightweight (single binary, 50MB footprint)
- 🔧 Easy configuration with sensible defaults

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Docker Setup](#docker-setup)
3. [Local Development Setup](#local-development-setup)
4. [Configuration](#configuration)
5. [Index Configuration](#index-configuration)
6. [Environment Variables](#environment-variables)
7. [Production Deployment](#production-deployment)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software
- **Docker** (v20.10+) and Docker Compose (v2.0+)
- **Python** 3.10+ with pip
- **Django** 4.2+ (already installed)

### Python Dependencies
Add to `requirements.txt`:
```txt
meilisearch>=0.31.0
```

Install:
```bash
pip install meilisearch>=0.31.0
```

---

## Docker Setup

### 1. Start MeiliSearch Container

The project includes a `docker-compose.yml` file with MeiliSearch pre-configured.

**Start services:**
```bash
docker-compose up -d meilisearch
```

**Verify MeiliSearch is running:**
```bash
docker-compose ps
# Expected output:
# NAME                    STATUS    PORTS
# portfolio_meilisearch   Up        0.0.0.0:7700->7700/tcp
```

**Check health:**
```bash
curl http://localhost:7700/health
# Expected: {"status":"available"}
```

### 2. Container Configuration

**docker-compose.yml** (already created):
```yaml
services:
  meilisearch:
    image: getmeili/meilisearch:v1.5
    container_name: portfolio_meilisearch
    restart: unless-stopped
    ports:
      - "7700:7700"
    environment:
      - MEILI_MASTER_KEY=masterKey123456789
      - MEILI_ENV=development
      - MEILI_NO_ANALYTICS=true
      - MEILI_HTTP_ADDR=0.0.0.0:7700
      - MEILI_DB_PATH=/meili_data
      - MEILI_LOG_LEVEL=INFO
    volumes:
      - meilisearch_data:/meili_data
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--spider", "http://localhost:7700/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**Key Configuration Options:**
- `MEILI_MASTER_KEY`: API key for authentication (change in production!)
- `MEILI_ENV`: `development` (verbose logs) or `production` (optimized)
- `MEILI_NO_ANALYTICS`: Disable telemetry
- `MEILI_DB_PATH`: Persistent data storage location
- `MEILI_LOG_LEVEL`: `DEBUG`, `INFO`, `WARN`, or `ERROR`

### 3. Stop/Restart Services

```bash
# Stop MeiliSearch
docker-compose stop meilisearch

# Restart MeiliSearch
docker-compose restart meilisearch

# Stop and remove containers (preserves data)
docker-compose down

# Stop and remove containers + data volumes
docker-compose down -v
```

---

## Local Development Setup

### Option 1: Docker (Recommended)

Use Docker Compose as described above.

### Option 2: Native Installation

**Download MeiliSearch binary:**
```bash
# Windows
curl -L https://install.meilisearch.com | pwsh

# Linux/macOS
curl -L https://install.meilisearch.com | sh
```

**Run MeiliSearch:**
```bash
# With master key
./meilisearch --master-key="masterKey123456789" --env="development"

# Custom port
./meilisearch --master-key="masterKey123456789" --http-addr="127.0.0.1:7700"
```

**Verify:**
```bash
curl http://localhost:7700/health
```

---

## Configuration

### Environment Variables

Add to `.env` file (already updated):
```properties
# MeiliSearch Configuration
MEILI_MASTER_KEY=masterKey123456789
MEILI_HOST=http://localhost:7700
MEILI_ENV=development
MEILI_NO_ANALYTICS=true
MEILI_INDEX_NAME=portfolio_search
```

**Production Environment Variables:**
```properties
# Production settings
MEILI_MASTER_KEY=<generate-strong-32-char-key>
MEILI_HOST=https://meilisearch.yourdomain.com
MEILI_ENV=production
MEILI_NO_ANALYTICS=true
MEILI_INDEX_NAME=portfolio_search_prod
```

### Django Settings

Add to `project/settings.py` (or create `project/settings/search.py`):
```python
# MeiliSearch Configuration
MEILISEARCH_HOST = env('MEILI_HOST', default='http://localhost:7700')
MEILISEARCH_MASTER_KEY = env('MEILI_MASTER_KEY', default='masterKey123456789')
MEILISEARCH_INDEX_NAME = env('MEILI_INDEX_NAME', default='portfolio_search')
MEILISEARCH_TIMEOUT = 5  # seconds
MEILISEARCH_BATCH_SIZE = 100  # documents per batch
```

---

## Index Configuration

### Primary Index: `portfolio_search`

**Create index programmatically** (in `apps/main/search_index.py`):
```python
import meilisearch
from django.conf import settings

client = meilisearch.Client(settings.MEILISEARCH_HOST, settings.MEILISEARCH_MASTER_KEY)

# Create index
index = client.index(settings.MEILISEARCH_INDEX_NAME)

# Configure searchable attributes (priority order)
index.update_searchable_attributes([
    'title',        # Highest priority
    'name',         # Alias for title
    'excerpt',      # Medium-high priority
    'description',  # Medium-high priority
    'tags',         # Medium priority
    'content',      # Medium-low priority
    'value',        # Medium-low priority (PersonalInfo)
    'meta_description'  # Lowest priority
])

# Configure filterable attributes
index.update_filterable_attributes([
    'model_type',
    'category',
    'type',
    'is_visible',
    'is_featured',
    'is_free',
    'difficulty',
    'severity_level',
    'status',
    'published_at',
    'updated_at'
])

# Configure sortable attributes
index.update_sortable_attributes([
    'published_at',
    'updated_at',
    'view_count',
    'rating',
    'order'
])

# Configure displayed attributes (returned in search results)
index.update_displayed_attributes([
    'id',
    'model_type',
    'model_id',
    'title',
    'name',
    'excerpt',
    'description',
    'url',
    'category',
    'category_display',
    'tags',
    'metadata',
    'search_category',
    'search_icon'
])
```

### Ranking Rules

MeiliSearch default ranking (in order):
1. **Words** - Number of matching query terms
2. **Typo** - Fewer typos = higher rank
3. **Proximity** - Closer words = higher rank
4. **Attribute** - Position in searchable attributes list
5. **Sort** - Custom sort criteria
6. **Exactness** - Exact matches = higher rank

**Custom ranking** (add featured/popular content boost):
```python
index.update_ranking_rules([
    'words',
    'typo',
    'proximity',
    'attribute',
    'sort',
    'exactness',
    'desc(is_featured)',  # Featured content ranks higher
    'desc(view_count)',   # Popular content ranks higher
    'desc(rating)',       # Highly-rated content ranks higher
    'desc(published_at)'  # Recent content ranks higher
])
```

### Typo Tolerance

**Default settings (works well for most cases):**
- 1 character: 0 typos allowed
- 2-4 characters: 1 typo allowed
- 5+ characters: 2 typos allowed

**Customize if needed:**
```python
index.update_typo_tolerance({
    'enabled': True,
    'minWordSizeForTypos': {
        'oneTypo': 4,   # 4+ chars = 1 typo
        'twoTypos': 8   # 8+ chars = 2 typos
    },
    'disableOnWords': ['django', 'python'],  # Never allow typos for these
    'disableOnAttributes': ['slug']  # Exact match required for slugs
})
```

### Stop Words

**Remove common Turkish/English words from search:**
```python
index.update_stop_words([
    # English
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    # Turkish
    'bir', 've', 'veya', 'ile', 'bu', 'şu', 'için', 'gibi', 'kadar'
])
```

### Synonyms

**Add synonyms for better search coverage:**
```python
index.update_synonyms({
    'js': ['javascript'],
    'py': ['python'],
    'ai': ['artificial intelligence', 'yapay zeka'],
    'ml': ['machine learning'],
    'security': ['güvenlik', 'cybersecurity']
})
```

---

## Index Management Commands

### Check Index Status
```bash
curl -X GET 'http://localhost:7700/indexes/portfolio_search' \
  -H "Authorization: Bearer masterKey123456789"
```

### Get Index Settings
```bash
curl -X GET 'http://localhost:7700/indexes/portfolio_search/settings' \
  -H "Authorization: Bearer masterKey123456789"
```

### Get Document Count
```bash
curl -X GET 'http://localhost:7700/indexes/portfolio_search/stats' \
  -H "Authorization: Bearer masterKey123456789"
```

### Delete Index (careful!)
```bash
curl -X DELETE 'http://localhost:7700/indexes/portfolio_search' \
  -H "Authorization: Bearer masterKey123456789"
```

---

## Production Deployment

### Security Hardening

1. **Generate Strong Master Key:**
```bash
# Generate 32-character random key
openssl rand -base64 32
```

2. **Use HTTPS Only:**
```properties
MEILI_HOST=https://meilisearch.yourdomain.com
```

3. **Restrict Network Access:**
- Bind to private network: `MEILI_HTTP_ADDR=10.0.0.5:7700`
- Use firewall rules to block public access
- Only allow Django app server to connect

4. **Enable Rate Limiting:**
- Configure reverse proxy (Nginx/Caddy) for rate limiting
- Limit to 100 requests/minute per IP

### Recommended Production Setup

**Use managed MeiliSearch Cloud** (easiest):
- Official service: https://www.meilisearch.com/cloud
- Auto-scaling, backups, monitoring included
- Pricing: Free tier available, paid plans from $29/month

**Self-hosted on VPS:**
```bash
# Docker Compose production config
version: '3.8'
services:
  meilisearch:
    image: getmeili/meilisearch:v1.5
    restart: always
    environment:
      - MEILI_MASTER_KEY=${MEILI_MASTER_KEY}  # From secure env
      - MEILI_ENV=production
      - MEILI_NO_ANALYTICS=true
      - MEILI_HTTP_ADDR=0.0.0.0:7700
      - MEILI_MAX_INDEXING_MEMORY=2048MB
      - MEILI_MAX_INDEXING_THREADS=4
    volumes:
      - /var/lib/meilisearch:/meili_data
    networks:
      - private_network
```

**Nginx reverse proxy:**
```nginx
server {
    listen 443 ssl http2;
    server_name meilisearch.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:7700;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;

        # Rate limiting
        limit_req zone=search_limit burst=10 nodelay;
    }
}
```

---

## Troubleshooting

### Connection Errors

**Problem:** `Connection refused` or `Cannot connect to MeiliSearch`

**Solutions:**
1. Check MeiliSearch is running: `docker-compose ps`
2. Verify port 7700 is not blocked: `telnet localhost 7700`
3. Check master key matches: `echo $MEILI_MASTER_KEY`
4. Review logs: `docker-compose logs meilisearch`

### Authentication Errors

**Problem:** `401 Unauthorized` or `Invalid API key`

**Solutions:**
1. Verify master key in `.env` matches `docker-compose.yml`
2. Restart MeiliSearch after key change: `docker-compose restart meilisearch`
3. Check Django settings: `MEILISEARCH_MASTER_KEY` value

### Indexing Errors

**Problem:** Documents not appearing in search

**Solutions:**
1. Check index exists: `curl http://localhost:7700/indexes`
2. Verify document count: `curl http://localhost:7700/indexes/portfolio_search/stats`
3. Review indexing tasks: `curl http://localhost:7700/tasks`
4. Check for failed tasks: `curl http://localhost:7700/tasks?status=failed`

### Performance Issues

**Problem:** Slow search responses (>100ms)

**Solutions:**
1. Increase memory: `MEILI_MAX_INDEXING_MEMORY=4096MB`
2. Add more threads: `MEILI_MAX_INDEXING_THREADS=8`
3. Reduce indexed fields (remove low-value fields)
4. Limit result count: `limit=20` in search queries
5. Enable caching in Django for repeated queries

---

## Quick Start Checklist

- [ ] Start MeiliSearch: `docker-compose up -d meilisearch`
- [ ] Verify health: `curl http://localhost:7700/health`
- [ ] Install Python client: `pip install meilisearch>=0.31.0`
- [ ] Update `.env` with `MEILI_MASTER_KEY`, `MEILI_HOST`, `MEILI_INDEX_NAME`
- [ ] Create Django settings for MeiliSearch in `project/settings.py`
- [ ] Run initial reindex: `python manage.py reindex_search --all`
- [ ] Test search API: `curl http://localhost:8000/api/search/?q=test`
- [ ] Monitor logs: `docker-compose logs -f meilisearch`

---

## Next Steps

1. ✅ Docker Compose setup completed
2. ✅ Environment variables configured
3. ✅ Documentation written
4. ⏳ Create `apps/main/search_index.py` (SearchIndexManager)
5. ⏳ Implement signal-based auto-indexing
6. ⏳ Build search API endpoint
7. ⏳ Create frontend search interface

---

**Status:** Setup Documentation Complete ✅
**Next Action:** Create SearchIndexManager class (Task 3)
