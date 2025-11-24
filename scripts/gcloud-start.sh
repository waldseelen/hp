#!/bin/bash
# =============================================================================
# Google Cloud Run Startup Script
# =============================================================================
# Optimized startup script for Google Cloud Run deployment

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

log "Starting Django Portfolio Site on Google Cloud Run..."

# Environment setup
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-portfolio_site.settings}
export PORT=${PORT:-8080}

log "Python: $(python --version)"
log "Working directory: $(pwd)"
log "Port: ${PORT}"
log "Settings module: ${DJANGO_SETTINGS_MODULE}"

# Verify required environment variables
REQUIRED_VARS=("DATABASE_URL" "SECRET_KEY")
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        error "Required environment variable $var is not set"
    fi
done

success "Environment variables validated"

# Wait for database to be ready (Google Cloud SQL)
log "Checking database connection..."
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

success "Database connection verified"

# Run database migrations
log "Running database migrations..."
if python manage.py migrate --noinput; then
    success "Database migrations completed"
else
    error "Database migrations failed"
fi

# Collect static files (if not done in build)
log "Collecting static files..."
if python manage.py collectstatic --noinput --clear; then
    success "Static files collected"
else
    warning "Static files collection skipped"
fi

# Warm up cache if Redis is available
if [ -n "$REDIS_URL" ]; then
    log "Warming up cache..."
    python -c "
from django.core.cache import cache
try:
    cache.set('health_check', 'ok', 60)
    print('Cache warmed up')
except Exception as e:
    print(f'Cache warmup failed: {e}')
" || warning "Cache warmup failed"
fi

success "Application startup complete"

# Configure Gunicorn for Google Cloud Run
WORKERS=${GUNICORN_WORKERS:-2}
THREADS=${GUNICORN_THREADS:-4}
TIMEOUT=${GUNICORN_TIMEOUT:-60}
WORKER_CLASS=${GUNICORN_WORKER_CLASS:-gthread}

log "Starting Gunicorn with $WORKERS workers and $THREADS threads..."

# Start Gunicorn
exec gunicorn portfolio_site.wsgi:application \
    --bind 0.0.0.0:${PORT} \
    --workers $WORKERS \
    --threads $THREADS \
    --worker-class $WORKER_CLASS \
    --worker-tmp-dir /dev/shm \
    --timeout $TIMEOUT \
    --graceful-timeout 30 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    --access-logformat '%h %l %u %t "%r" %s %b "%{Referer}i" "%{User-Agent}i" %D' \
    --log-level info
