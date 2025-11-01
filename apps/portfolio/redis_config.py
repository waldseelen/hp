"""
Production Redis Cache Configuration Examples

This module provides comprehensive Redis configuration examples for different
production environments and use cases.
"""

# Example 1: Basic Redis Configuration (Railway/Render/Heroku)
REDIS_CONFIG_BASIC = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",  # Railway/Render provides REDIS_URL
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 20,
                "retry_on_timeout": True,
                "socket_connect_timeout": 5,
                "socket_timeout": 5,
            },
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
            "SERIALIZER": "django_redis.serializers.json.JSONSerializer",
        },
        "KEY_PREFIX": "portfolio",
        "VERSION": 1,
        "TIMEOUT": 300,  # 5 minutes default
    }
}

# Example 2: High-Availability Redis Cluster Configuration
REDIS_CONFIG_CLUSTER = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": [
            "redis://redis-node-1:6379/1",
            "redis://redis-node-2:6379/1",
            "redis://redis-node-3:6379/1",
        ],
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.SentinelClient",
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 50,
                "retry_on_timeout": True,
                "socket_connect_timeout": 5,
                "socket_timeout": 5,
            },
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
            "SERIALIZER": "django_redis.serializers.json.JSONSerializer",
            "MASTER_NAME": "mymaster",  # Sentinel master name
        },
        "KEY_PREFIX": "portfolio",
        "VERSION": 1,
        "TIMEOUT": 600,  # 10 minutes for HA setup
    }
}

# Example 3: AWS ElastiCache Redis Configuration
REDIS_CONFIG_ELASTICACHE = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://my-cluster.xxxxxx.ng.0001.use1.cache.amazonaws.com:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 100,  # Higher for AWS
                "retry_on_timeout": True,
                "socket_connect_timeout": 10,  # AWS may have higher latency
                "socket_timeout": 10,
            },
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
            "SERIALIZER": "django_redis.serializers.json.JSONSerializer",
            "PASSWORD": "your-elasticache-auth-token",  # If using auth
        },
        "KEY_PREFIX": "portfolio",
        "VERSION": 1,
        "TIMEOUT": 1800,  # 30 minutes for cloud setup
    }
}

# Example 4: Google Cloud Memorystore Redis Configuration
REDIS_CONFIG_MEMORYSTORE = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://10.0.0.3:6379/1",  # Private IP from Memorystore
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 50,
                "retry_on_timeout": True,
                "socket_connect_timeout": 5,
                "socket_timeout": 5,
            },
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
            "SERIALIZER": "django_redis.serializers.json.JSONSerializer",
        },
        "KEY_PREFIX": "portfolio",
        "VERSION": 1,
        "TIMEOUT": 900,  # 15 minutes
    }
}

# Example 5: Session Storage Configuration
SESSION_REDIS_CONFIG = {
    "SESSION_ENGINE": "django.contrib.sessions.backends.cache",
    "SESSION_CACHE_ALIAS": "sessions",
    "sessions": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/2",  # Different DB for sessions
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 20,
                "retry_on_timeout": True,
            },
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
        },
        "KEY_PREFIX": "session",
        "VERSION": 1,
        "TIMEOUT": 86400,  # 24 hours for sessions
    },
}


# Environment-based configuration selector
def get_redis_config(environment="development"):
    """
    Get appropriate Redis configuration based on environment.

    Args:
        environment (str): Environment name ('development', 'staging', 'production')

    Returns:
        dict: Redis cache configuration
    """
    configs = {
        "development": {
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "unique-snowflake-dev",
            }
        },
        "staging": REDIS_CONFIG_BASIC,
        "production": REDIS_CONFIG_BASIC,  # Use cluster for high-traffic sites
    }

    return configs.get(environment, configs["development"])


# Performance monitoring configuration
REDIS_MONITORING_CONFIG = {
    "OPTIONS": {
        "CLIENT_CLASS": "django_redis.client.DefaultClient",
        "CONNECTION_POOL_KWARGS": {
            "max_connections": 20,
            "retry_on_timeout": True,
            "socket_connect_timeout": 5,
            "socket_timeout": 5,
        },
        # Enable Redis statistics collection
        "STATS": True,
    }
}

# Cache warming configuration for production
CACHE_WARMING_CONFIG = {
    "WARM_UP_ON_STARTUP": True,
    "WARM_UP_URLS": [
        "/",  # Home page
        "/personal/",  # Personal page
        "/blog/",  # Blog listing
        "/tools/",  # Tools page
    ],
    "WARM_UP_INTERVAL": 3600,  # Warm up every hour
}

# Backup and recovery configuration
REDIS_BACKUP_CONFIG = {
    "BACKUP_ENABLED": True,
    "BACKUP_INTERVAL": 86400,  # Daily backup
    "BACKUP_RETENTION": 7,  # Keep 7 days of backups
    "BACKUP_PATH": "/var/redis/backups/",
}

# Usage example in Django settings:
"""
# settings/production.py

import os
from portfolio.redis_config import get_redis_config, SESSION_REDIS_CONFIG

# Get Redis configuration for production
CACHES = get_redis_config('production')

# Override with environment-specific Redis URL if available
REDIS_URL = os.environ.get('REDIS_URL')
if REDIS_URL:
    CACHES['default']['LOCATION'] = REDIS_URL

# Add session configuration
CACHES.update(SESSION_REDIS_CONFIG)

# Additional production settings
CACHES['default']['OPTIONS'].update({
    'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
    'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
})
"""

# Health check configuration for Redis
REDIS_HEALTH_CHECK = {
    "LOCATION": "redis://127.0.0.1:6379/1",
    "OPTIONS": {
        "CLIENT_CLASS": "django_redis.client.DefaultClient",
        "CONNECTION_POOL_KWARGS": {
            "socket_connect_timeout": 1,
            "socket_timeout": 1,
        },
    },
    "KEY_PREFIX": "health",
    "TIMEOUT": 30,
}
