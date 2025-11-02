# Makefile for Django Portfolio Project
# Automates code quality, testing, and development tasks

.PHONY: help install format lint test clean build deploy

# Default target
help:
	@echo "Available commands:"
	@echo "  install        Install dependencies and setup development environment"
	@echo "  format         Format code with Black and isort"
	@echo "  lint           Run linting with flake8 and mypy"
	@echo "  test           Run tests with pytest"
	@echo "  test-ui        Run UI/UX specific tests"
	@echo "  test-coverage  Run tests with coverage report"
	@echo "  clean          Clean temporary files and caches"
	@echo "  build          Build CSS and collect static files"
	@echo "  pre-commit     Setup and run pre-commit hooks"
	@echo "  security       Run security checks"
	@echo "  check-all      Run all quality checks (format, lint, test, security)"

# Development setup
install:
	pip install -r requirements.txt
	npm install
	python manage.py migrate
	pre-commit install
	@echo "✅ Development environment setup complete"

# Code formatting
format:
	@echo "🎨 Formatting code with Black..."
	black . --exclude="migrations|staticfiles|node_modules"
	@echo "📦 Sorting imports with isort..."
	isort . --skip migrations --skip staticfiles --skip node_modules
	@echo "✅ Code formatting complete"

# Linting
lint:
	@echo "🔍 Running flake8..."
	flake8 --exclude=migrations,staticfiles,node_modules .
	@echo "🔍 Running mypy..."
	mypy . --exclude migrations --exclude staticfiles --exclude node_modules
	@echo "✅ Linting complete"

# Testing
test:
	@echo "🧪 Running tests..."
	pytest -v
	@echo "✅ Tests complete"

test-ui:
	@echo "🎨 Running UI/UX tests..."
	pytest -v -m "ui or visual or theme or animation or responsive or accessibility"
	@echo "✅ UI/UX tests complete"

test-coverage:
	@echo "📊 Running tests with coverage..."
	pytest --cov=apps --cov-report=html --cov-report=term-missing
	@echo "✅ Coverage report generated in htmlcov/"

test-integration:
	@echo "🔗 Running integration tests..."
	pytest -v -m "integration"
	@echo "✅ Integration tests complete"

test-visual:
	@echo "👁️ Running visual regression tests..."
	pytest -v -m "visual" --tb=short
	@echo "✅ Visual regression tests complete"

# Security checks
security:
	@echo "🔒 Running security checks with bandit..."
	bandit -r . -x tests,migrations,staticfiles,node_modules
	@echo "✅ Security checks complete"

# Pre-commit
pre-commit:
	@echo "🔧 Setting up pre-commit hooks..."
	pre-commit install
	@echo "🔧 Running pre-commit on all files..."
	pre-commit run --all-files
	@echo "✅ Pre-commit setup complete"

# Build
build:
	@echo "🏗️ Building CSS..."
	npm run build:css
	@echo "📦 Collecting static files..."
	python manage.py collectstatic --noinput
	@echo "✅ Build complete"

build-production:
	@echo "🏭 Building for production..."
	npm run build:all
	python manage.py collectstatic --noinput --clear
	@echo "✅ Production build complete"

# Cleanup
clean:
	@echo "🧹 Cleaning temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	@echo "✅ Cleanup complete"

# Django management
migrate:
	@echo "🗃️ Running migrations..."
	python manage.py migrate
	@echo "✅ Migrations complete"

makemigrations:
	@echo "🗃️ Creating migrations..."
	python manage.py makemigrations
	@echo "✅ Migrations created"

runserver:
	@echo "🚀 Starting development server..."
	python manage.py runserver

shell:
	@echo "🐚 Opening Django shell..."
	python manage.py shell

# Complete quality check
check-all: format lint test security
	@echo "✅ All quality checks passed!"

# UI/UX specific quality checks
check-ui: format lint test-ui
	@echo "🎨 UI/UX quality checks complete!"

# Quick development check
check-quick: format lint
	@echo "⚡ Quick quality checks complete!"

# Documentation
docs:
	@echo "📚 Generating documentation..."
	@echo "UI Kit available at: /ui-kit/"
	@echo "Test coverage report: htmlcov/index.html"
	@echo "✅ Documentation links provided"

# Development helpers
reset-db:
	@echo "⚠️ Resetting database..."
	rm -f db.sqlite3
	python manage.py migrate
	@echo "✅ Database reset complete"

create-superuser:
	@echo "👤 Creating superuser..."
	python manage.py createsuperuser

# Performance testing
test-performance:
	@echo "⚡ Running performance tests..."
	pytest -v -m "performance"
	@echo "✅ Performance tests complete"

# Accessibility testing
test-accessibility:
	@echo "♿ Running accessibility tests..."
	pytest -v -m "accessibility"
	@echo "✅ Accessibility tests complete"
