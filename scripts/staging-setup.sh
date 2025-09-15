#!/bin/bash
# =============================================================================
# Staging Environment Setup Script
# =============================================================================
# Configures staging environment with test data and development features

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

log "Setting up staging environment..."

# Check if we're in staging
if [ "$DJANGO_SETTINGS_MODULE" != "portfolio_site.settings.staging" ]; then
    export DJANGO_SETTINGS_MODULE="portfolio_site.settings.staging"
    log "Set Django settings to staging"
fi

# Wait for database
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

# Run migrations
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

# Create superuser for staging
log "Creating staging superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()

# Create admin user
if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@staging.local',
        password='staging123'
    )
    print('✅ Staging admin user created: admin/staging123')
else:
    print('ℹ️ Admin user already exists')

# Create test user
if not User.objects.filter(username='testuser').exists():
    user = User.objects.create_user(
        username='testuser',
        email='test@staging.local',
        password='test123'
    )
    print('✅ Test user created: testuser/test123')
else:
    print('ℹ️ Test user already exists')
"

# Load test data if enabled
if [ "$ENABLE_TEST_DATA" = "True" ] || [ "$ENABLE_TEST_DATA" = "true" ]; then
    log "Loading test data..."

    # Create test blog posts
    python manage.py shell -c "
from apps.blog.models import Post, Category
from django.contrib.auth import get_user_model
from django.utils import timezone
import random

User = get_user_model()
admin_user = User.objects.filter(username='admin').first()

if admin_user:
    # Create categories
    categories = ['Technology', 'Django', 'Python', 'Web Development', 'Tutorial']
    for cat_name in categories:
        category, created = Category.objects.get_or_create(
            name=cat_name,
            defaults={'slug': cat_name.lower().replace(' ', '-')}
        )
        if created:
            print(f'✅ Created category: {cat_name}')

    # Create blog posts
    post_titles = [
        'Getting Started with Django',
        'Building RESTful APIs',
        'Frontend Performance Optimization',
        'Database Design Best Practices',
        'Containerizing Django Applications',
        'Automated Testing Strategies',
        'Security in Web Applications',
        'Scaling Django Applications'
    ]

    for i, title in enumerate(post_titles):
        if not Post.objects.filter(title=title).exists():
            category = Category.objects.order_by('?').first()
            post = Post.objects.create(
                title=title,
                slug=title.lower().replace(' ', '-'),
                content=f'''
# {title}

This is a sample blog post for staging environment testing.

## Introduction

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

## Key Points

- Point one about {title.lower()}
- Point two with technical details
- Point three about best practices

## Conclusion

Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.

---

*This is test content for staging environment.*
                '''.strip(),
                excerpt=f'A comprehensive guide to {title.lower()} with practical examples and best practices.',
                author=admin_user,
                category=category,
                is_published=True,
                created_at=timezone.now() - timezone.timedelta(days=random.randint(1, 30))
            )
            print(f'✅ Created blog post: {title}')
"

    # Create test tools/projects
    python manage.py shell -c "
from apps.tools.models import Tool
from django.contrib.auth import get_user_model

User = get_user_model()
admin_user = User.objects.filter(username='admin').first()

if admin_user:
    tools_data = [
        {
            'name': 'Portfolio Website',
            'description': 'A modern Django-based portfolio website with advanced features.',
            'technology': 'Django, Python, PostgreSQL, Redis',
            'github_url': 'https://github.com/example/portfolio',
            'demo_url': 'https://portfolio-staging.railway.app',
        },
        {
            'name': 'Task Management API',
            'description': 'RESTful API for task management with user authentication.',
            'technology': 'Django REST Framework, JWT, Celery',
            'github_url': 'https://github.com/example/task-api',
        },
        {
            'name': 'Data Visualization Dashboard',
            'description': 'Interactive dashboard for data analysis and visualization.',
            'technology': 'React, D3.js, Django, Chart.js',
            'demo_url': 'https://dashboard-demo.example.com',
        },
    ]

    for tool_data in tools_data:
        if not Tool.objects.filter(name=tool_data['name']).exists():
            tool = Tool.objects.create(
                name=tool_data['name'],
                slug=tool_data['name'].lower().replace(' ', '-'),
                description=tool_data['description'],
                technology=tool_data['technology'],
                github_url=tool_data.get('github_url', ''),
                demo_url=tool_data.get('demo_url', ''),
                is_featured=True,
                created_by=admin_user
            )
            print(f'✅ Created tool: {tool_data[\"name\"]}')
"

    success "Test data loaded successfully"
else
    log "Test data loading disabled"
fi

# Warm up cache
if [ -n "$REDIS_URL" ]; then
    log "Warming up cache..."
    python manage.py shell -c "
from django.core.cache import cache
import json

# Warm up cache with common data
cache.set('staging_setup', True, 3600)
cache.set('health_check', 'ok', 60)

# Cache site settings
cache.set('site_info', {
    'name': 'Portfolio Site (Staging)',
    'version': '1.0.0-staging',
    'environment': 'staging'
}, 3600)

print('✅ Cache warmed up')
"
    success "Cache warmed up"
fi

# Create logs directory
log "Setting up logging..."
mkdir -p logs
touch logs/staging.log
chmod 664 logs/staging.log
success "Logging configured"

# Verify staging banner
log "Verifying staging configuration..."
python manage.py shell -c "
from django.conf import settings

# Check staging-specific settings
checks = [
    ('STAGING_BANNER', getattr(settings, 'STAGING_BANNER', False)),
    ('DEBUG', settings.DEBUG),
    ('ENVIRONMENT', 'staging'),
]

print('Staging Configuration:')
for name, value in checks:
    status = '✅' if value else '❌'
    print(f'  {status} {name}: {value}')

# Check database connection
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
    print('  ✅ Database connection: OK')
except Exception as e:
    print(f'  ❌ Database connection: {e}')

# Check cache connection
from django.core.cache import cache
try:
    cache.set('test', 'ok', 1)
    result = cache.get('test')
    if result == 'ok':
        print('  ✅ Cache connection: OK')
    else:
        print('  ❌ Cache connection: Failed')
except Exception as e:
    print(f'  ❌ Cache connection: {e}')
"

# Final health check
log "Running final health check..."
python manage.py check --deploy || warning "Deployment checks failed (expected in staging)"

success "Staging environment setup completed!"

log "Staging Environment Summary:"
log "  - Admin User: admin / staging123"
log "  - Test User: testuser / test123"
log "  - Environment: staging"
log "  - Debug Mode: enabled"
log "  - Test Data: $([ "$ENABLE_TEST_DATA" = "True" ] && echo "loaded" || echo "disabled")"
log "  - Health Endpoint: /health/"
log "  - Admin Panel: /admin/"

log "You can now access the staging environment!"