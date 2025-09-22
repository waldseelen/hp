#!/bin/bash
# =============================================================================
# Railway Production Startup Script
# =============================================================================
# Optimized startup script for Railway deployment with health checks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log "Starting Django Portfolio Site on Railway..."

# Check environment
log "Environment: ${DJANGO_SETTINGS_MODULE:-project.settings.production}"
log "Debug mode: ${DEBUG:-False}"
log "Port: ${PORT:-8000}"

# Verify required environment variables
REQUIRED_VARS=("DATABASE_URL" "SECRET_KEY")
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        error "Required environment variable $var is not set"
    fi
done

success "Environment variables validated"

# Wait for database to be ready
log "Waiting for database to be ready..."
timeout=60
counter=0

while ! python manage.py check --database default 2>/dev/null; do
    if [ $counter -ge $timeout ]; then
        error "Database not ready after ${timeout} seconds"
    fi
    log "Database not ready, waiting... ($counter/$timeout)"
    sleep 2
    counter=$((counter + 2))
done

success "Database is ready"

# Run database migrations
log "Running database migrations..."
if python manage.py migrate --noinput; then
    success "Database migrations completed"
else
    error "Database migrations failed"
fi

# Collect static files
log "Collecting static files..."
if python manage.py collectstatic --noinput --clear; then
    success "Static files collected"
else
    warning "Static files collection failed, continuing..."
fi

# Create superuser if needed (only in staging)
if [ "$DEBUG" = "True" ] && [ "$DJANGO_SETTINGS_MODULE" = "project.settings.development" ]; then
    log "Creating default superuser for staging..."
    python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@railway.app', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
" || warning "Could not create superuser"
fi

# Warm up cache if Redis is available
if [ -n "$REDIS_URL" ]; then
    log "Warming up cache..."
    python manage.py shell -c "
from django.core.cache import cache;
cache.set('health_check', 'ok', 60);
print('Cache warmed up')
" || warning "Cache warmup failed"
fi

# Verify health endpoint
log "Verifying application health..."
timeout=30
counter=0

# Start Django in background for health check
python manage.py runserver 0.0.0.0:${PORT:-8000} &
DJANGO_PID=$!

# Wait for Django to start
sleep 5

while ! curl -f "http://localhost:${PORT:-8000}/health/" >/dev/null 2>&1; do
    if [ $counter -ge $timeout ]; then
        kill $DJANGO_PID 2>/dev/null || true
        error "Health check failed after ${timeout} seconds"
    fi
    log "Waiting for health check... ($counter/$timeout)"
    sleep 2
    counter=$((counter + 2))
done

# Stop test server
kill $DJANGO_PID 2>/dev/null || true
sleep 2

success "Health check passed"

# Configure Gunicorn
WORKERS=${GUNICORN_WORKERS:-4}
WORKER_CLASS=${GUNICORN_WORKER_CLASS:-sync}
TIMEOUT=${GUNICORN_TIMEOUT:-30}
MAX_REQUESTS=${GUNICORN_MAX_REQUESTS:-1000}
MAX_REQUESTS_JITTER=${GUNICORN_MAX_REQUESTS_JITTER:-100}

log "Starting Gunicorn with $WORKERS workers..."

# Final startup
exec gunicorn portfolio_site.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers $WORKERS \
    --worker-class $WORKER_CLASS \
    --timeout $TIMEOUT \
    --max-requests $MAX_REQUESTS \
    --max-requests-jitter $MAX_REQUESTS_JITTER \
    --preload \
    --access-logfile - \
    --error-logfile - \
    --access-logformat '%h %l %u %t "%r" %s %b "%{Referer}i" "%{User-Agent}i" %D' \
    --log-level info