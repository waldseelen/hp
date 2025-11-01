"""
Configuration settings for Push Notification Service
===================================================

Centralized configuration using Pydantic BaseSettings
for environment variable management.
"""

import os
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "your-secret-key-change-in-production"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "0.0.0.0"]
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/portfolio_db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_POOL_SIZE: int = 10

    # Authentication
    REQUIRE_AUTH: bool = True
    JWT_SECRET_KEY: str = "your-jwt-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    API_KEY: Optional[str] = None

    # VAPID Keys for Web Push
    VAPID_PRIVATE_KEY: str = ""
    VAPID_PUBLIC_KEY: str = ""
    VAPID_SUBJECT: str = "mailto:admin@example.com"

    # Rate Limiting
    RATE_LIMIT_SUBSCRIPTION: str = "100/hour"
    RATE_LIMIT_NOTIFICATION: str = "50/hour"
    RATE_LIMIT_ANALYTICS: str = "200/hour"
    RATE_LIMIT_DEFAULT: str = "1000/hour"

    # Push Notification Settings
    NOTIFICATION_TTL: int = 86400  # 24 hours in seconds
    MAX_NOTIFICATION_SIZE: int = 4096  # 4KB
    MAX_BATCH_SIZE: int = 1000
    DELIVERY_RETRY_ATTEMPTS: int = 3
    DELIVERY_RETRY_DELAY: int = 300  # 5 minutes

    # External Services
    SENTRY_DSN: Optional[str] = None
    PROMETHEUS_METRICS_ENABLED: bool = True

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Security
    CORS_ALLOW_CREDENTIALS: bool = True
    SECURITY_HEADERS: bool = True

    # Background Tasks
    CLEANUP_INTERVAL_HOURS: int = 24
    RETENTION_DAYS: int = 90

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create settings instance
settings = Settings()


# Validation
if settings.ENVIRONMENT == "production":
    required_prod_vars = [
        "DATABASE_URL",
        "REDIS_URL",
        "VAPID_PRIVATE_KEY",
        "VAPID_PUBLIC_KEY",
        "JWT_SECRET_KEY",
    ]

    missing_vars = []
    for var in required_prod_vars:
        if not getattr(settings, var):
            missing_vars.append(var)

    if missing_vars:
        raise ValueError(
            f"Missing required production environment variables: {', '.join(missing_vars)}"
        )


# Database configuration
DATABASE_CONFIG = {
    "pool_size": settings.DATABASE_POOL_SIZE,
    "max_overflow": settings.DATABASE_MAX_OVERFLOW,
    "pool_pre_ping": True,
    "pool_recycle": 3600,
    "echo": settings.DEBUG and settings.ENVIRONMENT == "development",
}

# Redis configuration
REDIS_CONFIG = {
    "decode_responses": True,
    "max_connections": settings.REDIS_POOL_SIZE,
    "retry_on_timeout": True,
    "socket_keepalive": True,
    "socket_keepalive_options": {},
}

# Rate limit configuration
RATE_LIMITS = {
    "subscriptions": settings.RATE_LIMIT_SUBSCRIPTION,
    "notifications": settings.RATE_LIMIT_NOTIFICATION,
    "analytics": settings.RATE_LIMIT_ANALYTICS,
    "default": settings.RATE_LIMIT_DEFAULT,
}

# Push notification configuration
PUSH_CONFIG = {
    "ttl": settings.NOTIFICATION_TTL,
    "max_size": settings.MAX_NOTIFICATION_SIZE,
    "max_batch_size": settings.MAX_BATCH_SIZE,
    "retry_attempts": settings.DELIVERY_RETRY_ATTEMPTS,
    "retry_delay": settings.DELIVERY_RETRY_DELAY,
    "vapid": {
        "subject": settings.VAPID_SUBJECT,
        "private_key": settings.VAPID_PRIVATE_KEY,
        "public_key": settings.VAPID_PUBLIC_KEY,
    },
}
