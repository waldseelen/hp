#!/bin/bash
# =============================================================================
# Database Backup Script for Railway Deployment
# =============================================================================
# Automated database backup with rotation and cloud storage integration

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

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/tmp/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_PREFIX="portfolio_backup"

# Parse DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    error "DATABASE_URL environment variable is required"
fi

# Extract database connection info from DATABASE_URL
# Format: postgresql://user:password@host:port/database
DB_URL_REGEX="^postgresql://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+)$"

if [[ $DATABASE_URL =~ $DB_URL_REGEX ]]; then
    DB_USER="${BASH_REMATCH[1]}"
    DB_PASSWORD="${BASH_REMATCH[2]}"
    DB_HOST="${BASH_REMATCH[3]}"
    DB_PORT="${BASH_REMATCH[4]}"
    DB_NAME="${BASH_REMATCH[5]}"
else
    error "Invalid DATABASE_URL format"
fi

log "Starting database backup process..."
log "Database: $DB_NAME@$DB_HOST:$DB_PORT"
log "Backup directory: $BACKUP_DIR"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup filename
BACKUP_FILE="$BACKUP_DIR/${BACKUP_PREFIX}_${DB_NAME}_${TIMESTAMP}.sql"
COMPRESSED_BACKUP="$BACKUP_FILE.gz"

# Set PostgreSQL password
export PGPASSWORD="$DB_PASSWORD"

# Create database backup
log "Creating database backup..."
if pg_dump \
    --host="$DB_HOST" \
    --port="$DB_PORT" \
    --username="$DB_USER" \
    --dbname="$DB_NAME" \
    --verbose \
    --clean \
    --no-owner \
    --no-privileges \
    --format=plain \
    --file="$BACKUP_FILE"; then
    success "Database backup created: $BACKUP_FILE"
else
    error "Database backup failed"
fi

# Compress backup
log "Compressing backup..."
if gzip "$BACKUP_FILE"; then
    success "Backup compressed: $COMPRESSED_BACKUP"
    BACKUP_FILE="$COMPRESSED_BACKUP"
else
    warning "Backup compression failed, keeping uncompressed"
fi

# Get backup size
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
log "Backup size: $BACKUP_SIZE"

# Upload to cloud storage (if configured)
if [ -n "$AWS_S3_BUCKET" ] && command -v aws >/dev/null 2>&1; then
    log "Uploading backup to AWS S3..."
    S3_KEY="backups/database/$(basename "$BACKUP_FILE")"

    if aws s3 cp "$BACKUP_FILE" "s3://$AWS_S3_BUCKET/$S3_KEY" \
        --storage-class STANDARD_IA \
        --metadata "timestamp=$TIMESTAMP,database=$DB_NAME,size=$BACKUP_SIZE"; then
        success "Backup uploaded to S3: s3://$AWS_S3_BUCKET/$S3_KEY"
    else
        warning "S3 upload failed"
    fi
elif [ -n "$GCS_BUCKET" ] && command -v gsutil >/dev/null 2>&1; then
    log "Uploading backup to Google Cloud Storage..."
    GCS_PATH="gs://$GCS_BUCKET/backups/database/$(basename "$BACKUP_FILE")"

    if gsutil cp "$BACKUP_FILE" "$GCS_PATH"; then
        success "Backup uploaded to GCS: $GCS_PATH"
    else
        warning "GCS upload failed"
    fi
else
    log "No cloud storage configured, backup stored locally only"
fi

# Backup verification
log "Verifying backup integrity..."
if [ "${BACKUP_FILE##*.}" = "gz" ]; then
    if gzip -t "$BACKUP_FILE"; then
        success "Backup integrity verified (compressed)"
    else
        error "Backup verification failed (corrupted)"
    fi
else
    if [ -s "$BACKUP_FILE" ]; then
        success "Backup integrity verified (uncompressed)"
    else
        error "Backup verification failed (empty file)"
    fi
fi

# Clean up old backups
log "Cleaning up old backups (retention: $RETENTION_DAYS days)..."
OLD_BACKUPS=$(find "$BACKUP_DIR" -name "${BACKUP_PREFIX}_*.sql*" -mtime +$RETENTION_DAYS 2>/dev/null || true)

if [ -n "$OLD_BACKUPS" ]; then
    echo "$OLD_BACKUPS" | while read -r old_backup; do
        if [ -f "$old_backup" ]; then
            log "Removing old backup: $(basename "$old_backup")"
            rm -f "$old_backup"
        fi
    done
    success "Old backups cleaned up"
else
    log "No old backups to clean up"
fi

# Create backup metadata
METADATA_FILE="$BACKUP_DIR/${BACKUP_PREFIX}_${TIMESTAMP}.meta"
cat > "$METADATA_FILE" << EOF
{
    "timestamp": "$TIMESTAMP",
    "database": "$DB_NAME",
    "host": "$DB_HOST",
    "port": "$DB_PORT",
    "backup_file": "$(basename "$BACKUP_FILE")",
    "backup_size": "$BACKUP_SIZE",
    "compressed": $([ "${BACKUP_FILE##*.}" = "gz" ] && echo "true" || echo "false"),
    "created_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "retention_days": $RETENTION_DAYS
}
EOF

log "Backup metadata created: $METADATA_FILE"

# Summary
log "Backup Summary:"
log "  - Database: $DB_NAME"
log "  - Timestamp: $TIMESTAMP"
log "  - File: $(basename "$BACKUP_FILE")"
log "  - Size: $BACKUP_SIZE"
log "  - Location: $BACKUP_DIR"

success "Database backup completed successfully!"

# Cleanup environment
unset PGPASSWORD
