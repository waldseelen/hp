# Redis Configuration for Production Cache Invalidation

This document describes the recommended Redis configuration for production cache invalidation with Django.

## Overview

The intelligent cache invalidation system uses Redis to store cached data with smart invalidation based on Django model signals. This setup ensures consistent cache behavior across multiple application instances.

## Production Redis Configuration

### Installation

```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Docker (Recommended for production)
docker pull redis:7-alpine
docker run -d --name redis -p 6379:6379 redis:7-alpine redis-server --appendonly yes
```

### Configuration File (redis.conf)

```ini
# Redis Production Configuration
# Location: /etc/redis/redis.conf or docker volume

# Network
bind 127.0.0.1 ::1
protected-mode yes
port 6379
tcp-backlog 511
timeout 0
tcp-keepalive 300

# Persistence (RDB - Snapshot)
save 900 1        # Save after 900 seconds if at least 1 key changed
save 300 10       # Save after 300 seconds if at least 10 keys changed
save 60 10000     # Save after 60 seconds if at least 10000 keys changed

stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir ./

# Persistence (AOF - Append Only File)
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec  # Safer: fsync every second instead of every write
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# Memory Management
maxmemory 2gb
maxmemory-policy allkeys-lru  # Evict keys using LRU when max memory reached

# Client Management
maxclients 10000

# Performance Tuning
hz 10                    # Server refresh frequency
dynamic-hz yes          # Adaptive hz

# Replication (for high availability)
# role master or slave
# slave-read-only yes
# repl-backlog-size 1mb

# Security
requirepass your_redis_password_here
# Add ACL rules for production
# requirepass will be deprecated in favor of ACL

# Logging
loglevel notice
logfile ""  # Empty = stdout, or specify file path
syslog-enabled no

# Slowlog for monitoring
slowlog-log-slower-than 10000  # microseconds
slowlog-max-len 128

# Latency Monitoring
latency-monitor-threshold 0

# Keyspace Notifications (for pubsub features)
notify-keyspace-events ""
# Use "Ex" for key expiration events
# Use "AKE" for all events, key-space, and expiration
```

## Django Settings Configuration

### settings.py Cache Configuration

```python
# Cache Configuration for Production

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        # OR with password: "redis://:password@127.0.0.1:6379/1",
        # OR for multiple nodes: "redis://127.0.0.1:6379/1,redis://127.0.0.1:6380/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            # Connection Pool Options
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 50,
                "retry_on_timeout": True,
                "health_check_interval": 30,
            },
            # Parser Options
            "PARSER": "redis.connection.HiredisParser",
            # Compressor
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
            # Connection options
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
            "IGNORE_EXCEPTIONS": False,
            # Password (alternative to URL)
            # "PASSWORD": "your_redis_password_here",
            # SSL Support
            "SSL_CERT_REQS": "required",
            "SSL_CA_CERTS": "/path/to/ca-cert.pem",
        },
        "TIMEOUT": 900,  # 15 minutes default timeout
        "VERSION": 1,
        "KEY_PREFIX": "app",
    },
    # Separate cache for sessions (optional)
    "sessions": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/2",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# Session Cache Configuration (optional)
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "sessions"
SESSION_COOKIE_AGE = 86400  # 24 hours

# Cache Invalidation Configuration
CACHE_TIMEOUT_SHORT = 300      # 5 minutes
CACHE_TIMEOUT_MEDIUM = 900     # 15 minutes
CACHE_TIMEOUT_LONG = 3600      # 1 hour
CACHE_TIMEOUT_DAILY = 86400    # 24 hours

# Enable cache key versioning
CACHE_MIDDLEWARE_KEY_PREFIX = "portfolio_app"
CACHE_MIDDLEWARE_SECONDS = 600

# Cache Statistics and Monitoring
CACHE_STATS_ENABLED = True
```

### settings.py Installation Requirements

```python
# Add to INSTALLED_APPS in settings.py
INSTALLED_APPS = [
    # ...
    'django_redis',
    # ...
]

# Logging Configuration for Cache Operations
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/cache.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'apps.main.cache_utils': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'apps.main.signals': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django_redis': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

## Installation Commands

```bash
# Install required packages
pip install django-redis
pip install redis
pip install hiredis  # Performance optimization for redis-py

# Install requirements file
pip install -r requirements/production.txt
```

## Docker Compose Setup (Recommended for Production)

### docker-compose.yml

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: app_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
      - ./config/redis.conf:/usr/local/etc/redis/redis.conf:ro
    command: redis-server /usr/local/etc/redis/redis.conf
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - app_network
    restart: unless-stopped

  web:
    image: app:latest
    depends_on:
      redis:
        condition: service_healthy
    environment:
      REDIS_URL: redis://redis:6379/1
      REDIS_PASSWORD: ${REDIS_PASSWORD}
    networks:
      - app_network
    restart: unless-stopped

volumes:
  redis_data:

networks:
  app_network:
    driver: bridge
```

## Kubernetes Deployment (Enterprise)

### redis-statefulset.yaml

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: redis-config
data:
  redis.conf: |
    maxmemory 2gb
    maxmemory-policy allkeys-lru
    appendonly yes

---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
spec:
  serviceName: redis
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        volumeMounts:
        - name: data
          mountPath: /data
        - name: config
          mountPath: /usr/local/etc/redis
        livenessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 30
          periodSeconds: 10
      volumes:
      - name: config
        configMap:
          name: redis-config
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 10Gi
```

## Cache Invalidation Strategy

### Smart Invalidation Patterns

The application uses the following cache invalidation strategy:

1. **Model-Based Invalidation**: When a model instance is saved/deleted, related cache keys are automatically cleared
2. **Pattern Matching**: Supports wildcard patterns for batch invalidation (e.g., `home_page_data_*`)
3. **Fallback Mechanism**: When cache is unavailable, views return fallback data

### Cache Key Mapping

| Model | Cache Keys Affected |
|-------|------------------|
| PersonalInfo | home_page_data_*, personal_page_data, portfolio_statistics |
| SocialLink | home_page_data_*, personal_page_data |
| Post | home_page_data_*, blog_posts_* |
| Tool | home_page_data_*, tools_* |
| AITool | home_page_data_*, ai_tools_* |
| ContactMessage | portfolio_statistics |

## Monitoring and Maintenance

### Redis CLI Monitoring

```bash
# Connect to Redis
redis-cli

# Monitor commands in real-time
> MONITOR

# Get memory statistics
> INFO memory

# Get cache statistics
> INFO stats

# Get key count by type
> INFO keyspace

# Clear all cache (development only!)
> FLUSHDB    # Current database
> FLUSHALL   # All databases
```

### Performance Monitoring Commands

```bash
# Check slowlog (commands taking > 10ms)
redis-cli slowlog get 10

# Memory usage by key
redis-cli --bigkeys

# Find large keys
redis-cli --scan --pattern "*"

# Get eviction statistics
redis-cli INFO stats | grep evicted
```

### Health Check Script

```python
# cache_health_check.py
from django.core.cache import cache
from django.core.management.base import BaseCommand
import time

class Command(BaseCommand):
    help = 'Check Redis cache health'

    def handle(self, *args, **options):
        try:
            # Test basic operations
            start = time.time()
            cache.set('health_check', 'ok', 60)
            value = cache.get('health_check')
            elapsed = time.time() - start

            if value == 'ok':
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Cache is healthy (latency: {elapsed*1000:.2f}ms)'
                    )
                )
            else:
                self.stdout.write(self.style.ERROR('✗ Cache returned incorrect value'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Cache health check failed: {e}'))
```

Run with: `python manage.py cache_health_check`

## Troubleshooting

### Connection Issues

```python
# If getting "Connection refused" errors:
# 1. Verify Redis is running
redis-cli ping  # Should return: PONG

# 2. Check Redis configuration
redis-cli CONFIG GET port  # Should show 6379

# 3. Verify Django settings
python manage.py shell
>>> from django.core.cache import cache
>>> cache.set('test', 'value')
>>> cache.get('test')
```

### Memory Issues

```bash
# If Redis is running out of memory:
# 1. Check current usage
redis-cli INFO memory

# 2. Increase maxmemory in redis.conf
maxmemory 4gb

# 3. Restart Redis
sudo systemctl restart redis-server
```

### Performance Issues

```bash
# Check slowlog for slow queries
redis-cli slowlog get 10

# Monitor in real-time
redis-cli MONITOR

# Use pipeline for batch operations instead of individual sets
```

## Best Practices

1. **Always use Redis in production** - Local cache is not suitable for multi-instance deployments
2. **Enable persistence** - Use both RDB and AOF for data safety
3. **Monitor memory usage** - Set appropriate `maxmemory` policy
4. **Use connection pooling** - Django-redis handles this automatically
5. **Implement health checks** - Monitor Redis availability
6. **Set up logging** - Track cache operations for debugging
7. **Use key versioning** - Update `CACHE_MIDDLEWARE_KEY_PREFIX` to invalidate all cache after deployments
8. **Test failover scenarios** - Ensure application works even if Redis is temporarily unavailable

## Environment Variables

```bash
# .env (for local development)
REDIS_URL=redis://localhost:6379/1
REDIS_PASSWORD=your_secure_password

# production.env
REDIS_URL=redis://:${REDIS_PASSWORD}@redis.production.svc.cluster.local:6379/1
REDIS_PASSWORD=<very_secure_production_password>
```

## Performance Benchmarks

Expected performance with this setup:

- **Cache Hit**: ~1-5ms response time
- **Cache Miss with Fallback**: ~50-200ms (depends on query complexity)
- **Memory Usage**: ~500MB for typical portfolio app with 10k cache entries
- **Throughput**: ~10,000 operations/second on standard VM

## References

- [Django-Redis Documentation](https://niwinz.github.io/django-redis/)
- [Redis Official Documentation](https://redis.io/documentation)
- [Redis Best Practices](https://redis.io/docs/management/admin-hints/)
