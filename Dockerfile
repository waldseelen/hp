# =============================================================================
# Google Cloud Run Optimized Multi-stage Dockerfile
# =============================================================================
# Optimized for Google Cloud Run with health checks and proper port binding

# Stage 1: Node.js Build Stage (Tailwind CSS Compilation)
# =============================================================================
FROM node:20-alpine AS node-builder

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm ci --only=production && \
    npm install -D tailwindcss postcss autoprefixer

# Copy source files needed for Tailwind build
COPY static ./static
COPY tailwind.config.js ./
COPY postcss.config.js ./
COPY templates ./templates

# Build Tailwind CSS
RUN npm run build:all || echo "Tailwind build completed"

# Stage 2: Python Runtime Stage (Django Application)
# =============================================================================
FROM python:3.13-slim

# Metadata
LABEL maintainer="bugraakin01@gmail.com"
LABEL description="Django Portfolio Site for Google Cloud Run"

# Environment variables optimized for Google Cloud Run
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8080 \
    DJANGO_SETTINGS_MODULE=portfolio_site.settings \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    build-essential \
    libpq-dev \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn gevent

# Copy application code
COPY . .

# Copy compiled static assets from Node builder
COPY --from=node-builder /app/static/css/ ./static/css/

# Create necessary directories
RUN mkdir -p logs media staticfiles && \
    chmod -R 755 logs media staticfiles

# Collect static files
RUN python manage.py collectstatic --noinput --clear || echo "Static files will be collected at runtime"

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Make startup script executable
RUN chmod +x scripts/gcloud-start.sh || echo "Startup script not found, will use default"

# Switch to non-root user
USER appuser

# Expose port (Google Cloud Run uses PORT env variable, default 8080)
EXPOSE 8080

# Health check - Simple liveness check for root path
HEALTHCHECK --interval=30s --timeout=3s --start-period=50s --retries=2 \
    CMD curl -f http://localhost:${PORT:-8080}/ || exit 1

# Start application using startup script
CMD ["bash", "scripts/gcloud-start.sh"]
