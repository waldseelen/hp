# Multi-stage Build: Production-Ready Dockerfile for Google Cloud Run
# Django Backend + React/Vite Frontend
# Using Python-based image to avoid PEP 668 externally managed environment issues

# Stage 1: Build Frontend (Node.js)
FROM node:22-alpine AS frontend-builder

WORKDIR /app

COPY package*.json ./
ENV NODE_ENV=development
RUN npm install

COPY . .
RUN npm run build

# Stage 2: Production Runtime (Python-based)
FROM python:3.11-slim

WORKDIR /app

# Set Python environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies including Node.js for any runtime needs
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    postgresql-client \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy built frontend dist folder
COPY --from=frontend-builder /app/dist ./dist

# Copy Python dependencies
COPY requirements-prod.txt requirements.txt ./

# Install Python dependencies (no PEP 668 issues with official Python image)
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy entire project
COPY . .

# Collect Django static files
RUN python manage.py collectstatic --noinput || true

# Set environment for Cloud Run
ENV PORT=8080
ENV NODE_ENV=production
ENV DJANGO_SETTINGS_MODULE=project.settings.production

EXPOSE 8080

# Start Django with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "--timeout", "120", "project.wsgi:application"]