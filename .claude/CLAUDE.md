# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a modern Django portfolio website built with Django 5.1, featuring a comprehensive tech stack including Tailwind CSS, Progressive Web App (PWA) capabilities, push notifications, and advanced monitoring. The project follows Django best practices with a modular app structure, split settings, and comprehensive testing framework.

## Development Commands

### Core Django Commands
```bash
# Development server
python manage.py runserver

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Static files collection
python manage.py collectstatic --noinput

# Create superuser
python manage.py createsuperuser

# Django shell
python manage.py shell
```

### Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment file
copy .env.example .env
```

### Frontend Development
```bash
# Build CSS with Tailwind
npm run build:css
npm run build:components
npm run build:all

# Watch mode for development
npm run dev
npm run watch:css

# Optimization
npm run optimize:images
npm run optimize:fonts
```

### Testing
```bash
# Run Python tests
pytest
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest --cov           # With coverage

# Run JavaScript tests
npm run test
npm run test:js
npm run test:e2e
npm run test:coverage

# Linting and formatting
npm run lint:js
npm run lint:css
npm run format
```

## Architecture Overview

### Project Structure
- **`portfolio_site/`**: Core Django project with split settings architecture
  - **`settings/`**: Environment-specific settings (`base.py`, `development.py`, `production.py`)
  - **`urls.py`**: Main URL configuration
- **`apps/`**: Modular Django applications
  - **`main/`**: Core application with models, context processors, and utilities
  - **`blog/`**: Blog system with posts, categories, and search
  - **`tools/`**: Tools showcase application
  - **`contact/`**: Contact form and message handling
  - **`chat/`**: Chat application
- **`static/`**: Static assets (CSS, JS, images)
- **`templates/`**: Django templates with responsive design
- **`tests/`**: Comprehensive test suite

### Key Technologies
- **Backend**: Django 5.1, Python 3.11+, Django REST Framework
- **Database**: SQLite (development), PostgreSQL-ready
- **Frontend**: Tailwind CSS, Alpine.js, vanilla JavaScript
- **Testing**: pytest, pytest-django, Playwright, Vitest
- **Monitoring**: Sentry SDK, custom performance analytics
- **Security**: CSP headers, rate limiting, CORS
- **PWA**: Service workers, web push notifications, offline support

### Custom Features
- **Split Settings**: Environment-specific configuration management
- **Performance Monitoring**: Custom analytics with Core Web Vitals tracking
- **Security Headers**: Comprehensive CSP with nonce support
- **Push Notifications**: Web push with VAPID keys
- **Advanced Logging**: Structured logging with JSON formatting
- **Caching**: Redis integration for production
- **Image Optimization**: WebP/AVIF support with quality controls

## Development Guidelines

### Code Style and Standards
- Follow Django conventions and best practices
- Use Python type hints where appropriate
- Maintain test coverage above 85%
- Use semantic versioning for releases
- Follow PEP 8 for Python code styling

### Environment Management
- **Development**: Uses SQLite, debug mode enabled, console email backend
- **Production**: PostgreSQL, Redis caching, SMTP email, Sentry monitoring
- Settings are managed through environment variables using python-decouple
- Secret keys and sensitive data must be stored in `.env` file

### Testing Strategy
- **Unit Tests**: Individual function/method testing
- **Integration Tests**: Multi-component interaction testing
- **E2E Tests**: Full user workflow testing with Playwright
- Tests are organized by app and use pytest markers for categorization
- Coverage reports generated in HTML and XML formats

### Security Considerations
- CSP headers implemented with nonce-based inline script/style protection
- Rate limiting applied to all sensitive endpoints
- CORS properly configured for API endpoints
- Session and CSRF cookies secured in production
- Sentry integration for error monitoring and performance tracking

### Performance Optimization
- Static files served via WhiteNoise with compression
- Database queries optimized with select_related and prefetch_related
- Redis caching for session storage and data caching
- Image optimization with WebP/AVIF format support
- Service worker implementation for offline functionality

### Deployment Notes
- Docker configuration available with docker-compose.prod.yml
- Static files collection required before production deployment
- Database migrations must be run on each deployment
- Health check endpoint available at `/health/`
- Logging configured for production with file rotation

## Important Configuration Files

### Settings Architecture
- **`portfolio_site/settings/base.py`**: Shared settings across environments
- **`portfolio_site/settings/development.py`**: Development-specific settings
- **`portfolio_site/settings/production.py`**: Production-specific settings

### Environment Variables (`.env`)
Key variables that should be configured:
- `SECRET_KEY`: Django secret key (required for production)
- `DEBUG`: Debug mode (False for production)
- `ALLOWED_HOSTS`: Comma-separated allowed hostnames
- `DATABASE_URL`: Database connection string
- `REDIS_URL`: Redis connection for caching
- `SENTRY_DSN`: Error tracking and performance monitoring
- `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY`: Push notification keys
- Email configuration for contact forms

### Testing Configuration
- **`pytest.ini`**: Comprehensive pytest configuration with coverage settings
- Tests use Django's test database and are configured for parallel execution
- Coverage threshold set to 85% minimum

## Common Development Tasks

### Adding New Django Apps
1. Create app in `apps/` directory: `python manage.py startapp newapp apps/newapp`
2. Add to `INSTALLED_APPS` in `portfolio_site/settings/base.py`
3. Create URL patterns and include in main `urls.py`
4. Add appropriate tests in `tests/` directory

### Database Changes
1. Make model changes in appropriate app
2. Generate migrations: `python manage.py makemigrations`
3. Apply migrations: `python manage.py migrate`
4. Update tests and fixtures as needed

### Static Asset Updates
1. Modify source files in `static/css/` or `static/js/`
2. Run Tailwind build: `npm run build:all`
3. Collect static files: `python manage.py collectstatic`
4. Test changes in both development and production modes

### Performance Monitoring
- Performance metrics automatically tracked for Core Web Vitals
- Custom analytics available through `main.analytics` module
- Sentry integration provides error tracking and performance insights
- Database query optimization tracked in development mode


@- @task.txt oku ve denileni yap doğrudan başla veya devam veya go dediğimde

# 🚨 CRITICAL IMPLEMENTATION RULE - NEVER FORGET 🚨

## THE FUNDAMENTAL MISTAKE TO NEVER REPEAT:

**NEVER TRUST THE ROADMAP CHECKMARKS (✅) WITHOUT VERIFYING ACTUAL IMPLEMENTATION**

### What I Did Wrong:
1. ❌ Looked at roadmap.txt checkmarks and assumed tasks were complete
2. ❌ Did not verify actual code implementation in the project
3. ❌ Skipped verification steps assuming they were already done
4. ❌ Marked things as complete without testing functionality

### What I MUST Always Do:
1. ✅ **READ THE ACTUAL CODE** - Never trust roadmap status
2. ✅ **TEST THE FUNCTIONALITY** - Run and verify every feature works
3. ✅ **FIND MISSING PIECES** - Look for incomplete implementations
4. ✅ **COMPLETE THE WORK** - Actually implement what's missing
5. ✅ **VERIFY EVERYTHING** - Test every aspect before marking complete

### The User's Correct Approach:
- User said: "sen roadmap i değil ordaki işleri projemde kontrol etcen"
- Translation: "You should check the actual work in my project, not the roadmap"
- User was frustrated because I kept skipping actual implementation

### Real Example - Django i18n:
- ❌ Roadmap showed: "✅ Task 4.1: Django i18n Implementation - COMPLETE"
- ✅ Reality check: Templates had NO {% trans %} tags at all
- ✅ Actual work needed: Add {% load i18n %} and {% trans %} to ALL templates
- ✅ User was right: Implementation was completely missing

### NEVER FORGET RULE:
**"ROADMAP CHECKMARKS MEAN NOTHING - ONLY REAL CODE MATTERS"**

## Implementation Verification Checklist:

For EVERY task, I must:
1. 🔍 Read the actual files mentioned in the task
2. 🧪 Test the functionality described
3. 📋 Check if all code components exist
4. ⚙️ Verify configurations work
5. 🚀 Test the feature end-to-end
6. ✅ Only then mark as actually complete

**This is the most important rule in this entire project. NEVER skip verification.**
