# =============================================================================
# Multi-Stage Dockerfile for Django Portfolio Site
# =============================================================================
# Stage 1: Build dependencies and static assets
# Stage 2: Production runtime with minimal footprint
#
# Features:
# - Multi-stage build for smaller final image
# - Layer caching optimization
# - Non-root user for security
# - Health checks included
# - Development/Production variants
# =============================================================================

# =============================================================================
# BASE STAGE - Common dependencies
# =============================================================================
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies (layer cached separately)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
ARG APP_USER=django
ARG APP_UID=1000
ARG APP_GID=1000
RUN groupadd -g ${APP_GID} ${APP_USER} && \
    useradd -u ${APP_UID} -g ${APP_GID} -m -s /bin/bash ${APP_USER}

# Set working directory
WORKDIR /app

# =============================================================================
# BUILDER STAGE - Install Python dependencies
# =============================================================================
FROM base as builder

# Copy requirements first (better caching)
COPY requirements.txt requirements-django.txt ./

# Install Python dependencies to local directory
RUN pip install --user --no-warn-script-location \
    -r requirements.txt \
    -r requirements-django.txt

# =============================================================================
# FRONTEND STAGE - Build static assets
# =============================================================================
FROM node:18-alpine as frontend

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install Node.js dependencies
RUN npm ci --only=production

# Copy source files and build
COPY . .
RUN npm run build:all

# =============================================================================
# DEVELOPMENT STAGE
# =============================================================================
FROM base as development

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/${APP_USER}/.local

# Update PATH to include user site packages
ENV PATH="/home/${APP_USER}/.local/bin:${PATH}"

# Install development dependencies
RUN pip install --user \
    pytest \
    pytest-django \
    pytest-cov \
    black \
    isort \
    flake8 \
    mypy \
    bandit \
    safety

# Copy source code
COPY --chown=${APP_USER}:${APP_USER} . .

# Copy frontend assets
COPY --from=frontend --chown=${APP_USER}:${APP_USER} /app/static/css/output.css ./static/css/

# Switch to non-root user
USER ${APP_USER}

# Health check for development
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Development command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# =============================================================================
# PRODUCTION STAGE
# =============================================================================
FROM base as production

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/${APP_USER}/.local

# Update PATH to include user site packages
ENV PATH="/home/${APP_USER}/.local/bin:${PATH}"

# Install production-only dependencies
RUN pip install --user gunicorn

# Copy source code (excluding development files)
COPY --chown=${APP_USER}:${APP_USER} \
    apps/ ./apps/
COPY --chown=${APP_USER}:${APP_USER} \
    portfolio_site/ ./portfolio_site/
COPY --chown=${APP_USER}:${APP_USER} \
    templates/ ./templates/
COPY --chown=${APP_USER}:${APP_USER} \
    locale/ ./locale/
COPY --chown=${APP_USER}:${APP_USER} \
    manage.py ./

# Copy static directory structure
COPY --chown=${APP_USER}:${APP_USER} static/ ./static/

# Copy built frontend assets
COPY --from=frontend --chown=${APP_USER}:${APP_USER} /app/static/css/output.css ./static/css/

# Create necessary directories
RUN mkdir -p /app/staticfiles /app/media /app/logs && \
    chown -R ${APP_USER}:${APP_USER} /app/staticfiles /app/media /app/logs

# Create health check script
COPY --chown=${APP_USER}:${APP_USER} <<'EOF' /app/health_check.py
#!/usr/bin/env python
"""Health check script for Django application."""
import os
import sys
import django
import requests
from django.core.management import execute_from_command_line

def main():
    """Run health checks."""
    try:
        # Quick check - just test if Django can import
        if '--quick' in sys.argv:
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portfolio_site.settings.production')
            django.setup()
            print("Django health check: OK")
            return

        # Full check - test HTTP endpoint
        response = requests.get('http://localhost:8000/health/', timeout=5)
        if response.status_code == 200:
            print("HTTP health check: OK")
        else:
            print(f"HTTP health check: FAILED ({response.status_code})")
            sys.exit(1)
    except Exception as e:
        print(f"Health check failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
EOF

# Make health check executable
RUN chmod +x /app/health_check.py

# Switch to non-root user
USER ${APP_USER}

# Set Django settings for production
ENV DJANGO_SETTINGS_MODULE=portfolio_site.settings.production

# Health check for production
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python health_check.py --quick

# Expose port
EXPOSE 8000

# Production startup script
COPY --chown=${APP_USER}:${APP_USER} <<'EOF' /app/start_production.sh
#!/bin/bash
set -e

echo "Starting Django production server..."

# Wait for database
echo "Waiting for database..."
while ! python manage.py check --database default 2>/dev/null; do
    echo "Database not ready, waiting..."
    sleep 2
done

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Starting Gunicorn..."
exec gunicorn portfolio_site.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers ${GUNICORN_WORKERS:-4} \
    --worker-class ${GUNICORN_WORKER_CLASS:-sync} \
    --timeout ${GUNICORN_TIMEOUT:-30} \
    --max-requests ${GUNICORN_MAX_REQUESTS:-1000} \
    --max-requests-jitter ${GUNICORN_MAX_REQUESTS_JITTER:-100} \
    --preload \
    --access-logfile - \
    --error-logfile -
EOF

# Make startup script executable
RUN chmod +x /app/start_production.sh

# Production command
CMD ["/app/start_production.sh"]

# =============================================================================
# METADATA
# =============================================================================
LABEL maintainer="Portfolio Site Team"
LABEL version="1.0"
LABEL description="Django Portfolio Site - Multi-stage Docker build"
