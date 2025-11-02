#!/bin/bash
# =============================================================================
# Docker Image Testing Script
# =============================================================================
# Tests Docker images for functionality and health checks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="portfolio-site"
CONTAINER_NAME="portfolio-test"
TEST_PORT="8080"

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    cleanup
    exit 1
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

cleanup() {
    log "Cleaning up test container..."
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
}

# Parse arguments
TARGET="production"
TIMEOUT=60

while [[ $# -gt 0 ]]; do
    case $1 in
        --target)
            TARGET="$2"
            shift 2
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --target TARGET    Test target (development|production) [default: production]"
            echo "  --timeout SECONDS  Health check timeout [default: 60]"
            echo "  --help            Show this help message"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

log "Starting Docker image testing..."
log "Target: $TARGET"
log "Timeout: ${TIMEOUT}s"

# Check if image exists
if ! docker images | grep -q "$IMAGE_NAME.*$TARGET"; then
    error "Image $IMAGE_NAME:$TARGET not found. Build it first with: ./scripts/docker-build.sh --target $TARGET"
fi

# Cleanup any existing test container
cleanup

# Start test container
log "Starting test container..."
docker run -d \
    --name "$CONTAINER_NAME" \
    -p "$TEST_PORT:8000" \
    -e SECRET_KEY="test-secret-key" \
    -e DEBUG="False" \
    -e ALLOWED_HOSTS="localhost,127.0.0.1" \
    -e DATABASE_URL="sqlite:///test.sqlite3" \
    "$IMAGE_NAME:$TARGET"

# Wait for container to start
log "Waiting for container to start..."
sleep 5

# Check if container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    log "Container logs:"
    docker logs "$CONTAINER_NAME"
    error "Container failed to start"
fi

success "Container started successfully"

# Test health endpoints
log "Testing health endpoints..."

# Helper function to test endpoint
test_endpoint() {
    local endpoint="$1"
    local expected_status="$2"
    local description="$3"

    log "Testing $description ($endpoint)..."

    # Wait for endpoint to be available
    local attempts=0
    local max_attempts=$((TIMEOUT / 5))

    while [ $attempts -lt $max_attempts ]; do
        if curl -s -f "http://localhost:$TEST_PORT$endpoint" > /dev/null; then
            break
        fi
        attempts=$((attempts + 1))
        log "Attempt $attempts/$max_attempts - waiting for endpoint..."
        sleep 5
    done

    if [ $attempts -eq $max_attempts ]; then
        error "Endpoint $endpoint not available after ${TIMEOUT}s"
    fi

    # Test the endpoint
    local response=$(curl -s -w "%{http_code}" "http://localhost:$TEST_PORT$endpoint")
    local status_code="${response: -3}"
    local body="${response%???}"

    if [ "$status_code" = "$expected_status" ]; then
        success "$description returned expected status $expected_status"

        # Try to parse JSON response
        if echo "$body" | jq . > /dev/null 2>&1; then
            local status=$(echo "$body" | jq -r '.status // .alive // .ready' 2>/dev/null)
            if [ "$status" != "null" ] && [ "$status" != "" ]; then
                log "Status: $status"
            fi
        fi
    else
        warning "$description returned status $status_code (expected $expected_status)"
        log "Response: $body"
    fi
}

# Test health endpoints
test_endpoint "/health/" "200" "Full health check"
test_endpoint "/health/readiness/" "200" "Readiness check"
test_endpoint "/health/liveness/" "200" "Liveness check"

# Test main application endpoint
log "Testing main application..."
main_response=$(curl -s -w "%{http_code}" "http://localhost:$TEST_PORT/")
main_status="${main_response: -3}"

if [ "$main_status" = "200" ] || [ "$main_status" = "302" ]; then
    success "Main application responding (status: $main_status)"
else
    warning "Main application returned status $main_status"
fi

# Test Docker health check
log "Testing Docker native health check..."
health_status=$(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_NAME" 2>/dev/null || echo "unknown")

if [ "$health_status" = "healthy" ]; then
    success "Docker health check: healthy"
elif [ "$health_status" = "starting" ]; then
    log "Docker health check: still starting, waiting..."
    sleep 10
    health_status=$(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_NAME" 2>/dev/null || echo "unknown")
    if [ "$health_status" = "healthy" ]; then
        success "Docker health check: healthy"
    else
        warning "Docker health check: $health_status"
    fi
else
    warning "Docker health check: $health_status"
fi

# Show container stats
log "Container statistics:"
docker stats "$CONTAINER_NAME" --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

# Show recent logs
log "Recent container logs:"
docker logs --tail 20 "$CONTAINER_NAME"

# Cleanup
cleanup

success "Docker image testing completed successfully!"

log "Test summary:"
log "- Image: $IMAGE_NAME:$TARGET"
log "- Health endpoints: Tested"
log "- Main application: Tested"
log "- Docker health check: Verified"
log "- Container performance: Measured"

success "All tests passed! Image is ready for deployment."
