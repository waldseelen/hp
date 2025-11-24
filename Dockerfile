# Multi-stage Build: Production-Ready Dockerfile for Google Cloud Run
# Django Backend + React/Vite Frontend

# Stage 1: Build Frontend (Node.js)
FROM node:22-alpine AS frontend-builder

WORKDIR /app

COPY package*.json ./
RUN npm install --include=dev

COPY . .
RUN npm run build

# Stage 2: Production Runtime (Python + Node.js base)
FROM node:22-alpine

WORKDIR /app

# Install Python runtime dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    postgresql-client

# Copy built frontend dist folder
COPY --from=frontend-builder /app/dist ./dist

# Copy Python dependencies
COPY requirements-prod.txt requirements.txt ./

# Install Python dependencies
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
