#!/bin/bash
# =============================================================================
# Docker Build Optimization Script
# =============================================================================
# This script optimizes Docker builds with layer caching and parallel builds

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="portfolio-site"
REGISTRY="ghcr.io/waldseelen"
CACHE_FROM="type=gha"
CACHE_TO="type=gha,mode=max"

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

# Parse arguments
TARGET="production"
PUSH=false
NO_CACHE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --target)
            TARGET="$2"
            shift 2
            ;;
        --push)
            PUSH=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --target TARGET    Build target (development|production) [default: production]"
            echo "  --push            Push image to registry after build"
            echo "  --no-cache        Disable build cache"
            echo "  --help            Show this help message"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Validate target
if [[ "$TARGET" != "development" && "$TARGET" != "production" ]]; then
    error "Invalid target: $TARGET. Must be 'development' or 'production'"
fi

log "Starting Docker build process..."
log "Target: $TARGET"
log "Push: $PUSH"
log "Cache: $([ "$NO_CACHE" = true ] && echo "disabled" || echo "enabled")"

# Check if Docker buildx is available
if ! docker buildx version &> /dev/null; then
    error "Docker buildx is required but not available"
fi

# Create builder if it doesn't exist
BUILDER_NAME="portfolio-builder"
if ! docker buildx inspect "$BUILDER_NAME" &> /dev/null; then
    log "Creating buildx builder: $BUILDER_NAME"
    docker buildx create --name "$BUILDER_NAME" --use --bootstrap
else
    docker buildx use "$BUILDER_NAME"
fi

# Build arguments
BUILD_ARGS=""
CACHE_ARGS=""

if [ "$NO_CACHE" != true ]; then
    CACHE_ARGS="--cache-from $CACHE_FROM --cache-to $CACHE_TO"
fi

# Image tags
BASE_TAG="$REGISTRY/$IMAGE_NAME:$TARGET"
LATEST_TAG="$REGISTRY/$IMAGE_NAME:latest"

if [ "$TARGET" = "production" ]; then
    TAGS="--tag $BASE_TAG --tag $LATEST_TAG"
else
    TAGS="--tag $BASE_TAG"
fi

# Build command
BUILD_CMD="docker buildx build \
    --target $TARGET \
    --platform linux/amd64,linux/arm64 \
    $CACHE_ARGS \
    $TAGS \
    --progress=plain \
    ."

if [ "$PUSH" = true ]; then
    BUILD_CMD="$BUILD_CMD --push"
else
    BUILD_CMD="$BUILD_CMD --load"
fi

log "Building Docker image..."
log "Command: $BUILD_CMD"

# Execute build
if eval $BUILD_CMD; then
    success "Docker build completed successfully"

    # Show image info
    if [ "$PUSH" != true ]; then
        log "Image information:"
        docker images | grep "$IMAGE_NAME" | head -5

        # Show image size
        SIZE=$(docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}" | grep "$IMAGE_NAME:$TARGET" | awk '{print $2}')
        log "Image size: $SIZE"
    fi

    success "Build process completed!"
else
    error "Docker build failed"
fi

# Cleanup
log "Cleaning up unused images..."
docker image prune -f

success "Docker build optimization script completed!"