# =============================================================================
# Multi-stage Dockerfile for Django + Tailwind CSS v4
# =============================================================================
# This Dockerfile bypasses Railway's Nixpacks auto-detection completely

# Stage 1: Node.js Build Stage (Tailwind CSS Compilation)
# =============================================================================
FROM node:20-alpine AS node-builder

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy source files needed for Tailwind build
COPY static ./static
COPY tailwind.config.js ./
COPY postcss.config.js ./

# Build Tailwind CSS
RUN npm run build:all

# Stage 2: Python Runtime Stage (Django Application)
# =============================================================================
FROM python:3.13-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application code
COPY . .

# Copy compiled static assets from Node builder
COPY --from=node-builder /app/static/css/output.css ./static/css/output.css
COPY --from=node-builder /app/static/css/components/components-compiled.css ./static/css/components/components-compiled.css

# Collect static files (now all dependencies are available)
RUN python manage.py collectstatic --noinput --clear || echo "Collectstatic skipped (run at startup)"

# Make startup script executable
RUN chmod +x scripts/railway-start.sh

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health/ || exit 1

# Start application using railway-start.sh
CMD ["bash", "scripts/railway-start.sh"]
