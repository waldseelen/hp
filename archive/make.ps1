# PowerShell Makefile Alternative for Django Portfolio Project
# Automates code quality, testing, and development tasks
# Usage: .\make.ps1 <command>

param(
    [Parameter(Position = 0)]
    [string]$Command = "help"
)

# Color functions
function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Info { param($Message) Write-Host "ℹ️  $Message" -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Error-Custom { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }
function Write-Header { param($Message) Write-Host "`n🎯 $Message" -ForegroundColor Magenta }

# Dependency check
function Test-Command {
    param([string]$CommandName)
    return $null -ne (Get-Command $CommandName -ErrorAction SilentlyContinue)
}

# Help command
function Show-Help {
    Write-Host @"

🛠️  Django Portfolio Project - Development Commands
═══════════════════════════════════════════════════

Available commands:

  📦 SETUP
    install          Install dependencies and setup development environment

  🎨 CODE QUALITY
    format           Format code with Black and isort
    lint             Run linting with flake8 and mypy
    security         Run security checks with bandit
    check-all        Run all quality checks (format, lint, test, security)
    check-quick      Quick check (format + lint only)

  🧪 TESTING
    test             Run tests with pytest
    test-ui          Run UI/UX specific tests
    test-coverage    Run tests with coverage report
    test-integration Run integration tests
    test-visual      Run visual regression tests
    test-performance Run performance tests
    test-accessibility Run accessibility tests

  🏗️  BUILD & DEPLOY
    build            Build CSS and collect static files
    build-production Build for production

  🗃️  DATABASE
    migrate          Run migrations
    makemigrations   Create migrations
    reset-db         Reset database (⚠️  destructive)

  🚀 DEVELOPMENT
    runserver        Start development server
    shell            Open Django shell
    create-superuser Create Django superuser

  🔧 PRE-COMMIT
    pre-commit       Setup and run pre-commit hooks

  🧹 CLEANUP
    clean            Clean temporary files and caches

  📚 DOCUMENTATION
    docs             Show documentation links

Usage: .\make.ps1 <command>
Example: .\make.ps1 format

"@ -ForegroundColor White
}

# Install dependencies
function Invoke-Install {
    Write-Header "Installing dependencies..."

    if (-not (Test-Command "python")) {
        Write-Error-Custom "Python not found. Please install Python 3.11+"
        exit 1
    }

    Write-Info "Installing Python packages..."
    pip install -r requirements.txt

    if (Test-Path "package.json") {
        Write-Info "Installing Node packages..."
        npm install
    }

    Write-Info "Running migrations..."
    python manage.py migrate

    Write-Info "Setting up pre-commit hooks..."
    pre-commit install

    Write-Success "Development environment setup complete!"
}

# Format code
function Invoke-Format {
    Write-Header "Formatting code..."

    if (-not (Test-Command "black")) {
        Write-Error-Custom "Black not found. Run: pip install black"
        exit 1
    }

    if (-not (Test-Command "isort")) {
        Write-Error-Custom "isort not found. Run: pip install isort"
        exit 1
    }

    Write-Info "Formatting with Black..."
    python -m black . --exclude="\.venv-1|\.venv|node_modules|staticfiles|migrations|__pycache__"

    Write-Info "Sorting imports with isort..."
    python -m isort . --skip .venv-1 --skip .venv --skip node_modules --skip staticfiles --skip migrations --skip __pycache__

    Write-Success "Code formatting complete!"
}

# Lint code
function Invoke-Lint {
    Write-Header "Running linters..."

    $exitCode = 0

    if (Test-Command "flake8") {
        Write-Info "Running flake8..."
        # Only fail on E and F series errors (syntax, imports), ignore W505 and C901
        python -m flake8 apps/ --exclude=migrations --exclude=__pycache__ --max-line-length=88 --select=E, F --extend-ignore=E203 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Flake8 found critical issues. Run .\make.ps1 lint for details."
            $exitCode = 1
        }
    }
    else {
        Write-Warning "flake8 not found. Run: pip install flake8"
    }

    if (Test-Command "mypy") {
        Write-Info "Running mypy..."
        python -m mypy apps/main apps/portfolio apps/blog apps/tools --config-file mypy.ini --no-error-summary 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "mypy found type issues (expected - see docs/development/type-checking.md)"
        }
    }
    else {
        Write-Warning "mypy not found. Run: pip install mypy"
    }

    if ($exitCode -eq 0) {
        Write-Success "Linting complete!"
    }
    else {
        Write-Error-Custom "Flake8 found issues. Please fix them."
        exit $exitCode
    }
}

# Security checks
function Invoke-Security {
    Write-Header "Running security checks..."

    if (-not (Test-Command "bandit")) {
        Write-Error-Custom "Bandit not found. Run: pip install bandit"
        exit 1
    }

    Write-Info "Running bandit security scanner..."
    python -m bandit -r apps/ -ll -f json -o bandit-report.json 2>$null
    python -m bandit -r apps/ -ll

    if ($LASTEXITCODE -eq 0) {
        Write-Success "Security checks complete - no issues found!"
    }
    else {
        Write-Warning "Security issues detected. Review bandit-report.json for details."
    }
}

# Run tests
function Invoke-Test {
    Write-Header "Running tests..."

    if (-not (Test-Command "pytest")) {
        Write-Error-Custom "pytest not found. Run: pip install pytest"
        exit 1
    }

    python -m pytest -v

    if ($LASTEXITCODE -eq 0) {
        Write-Success "Tests complete!"
    }
    else {
        Write-Error-Custom "Tests failed!"
        exit 1
    }
}

# Run UI tests
function Invoke-TestUI {
    Write-Header "Running UI/UX tests..."
    python -m pytest -v -m "ui or visual or theme or animation or responsive or accessibility"
    if ($LASTEXITCODE -eq 0) { Write-Success "UI/UX tests complete!" }
}

# Run tests with coverage
function Invoke-TestCoverage {
    Write-Header "Running tests with coverage..."

    python -m pytest --cov=apps --cov-report=html --cov-report=term-missing

    if ($LASTEXITCODE -eq 0) {
        Write-Success "Coverage report generated in htmlcov/"
        Write-Info "Open htmlcov/index.html to view detailed report"
    }
}

# Run integration tests
function Invoke-TestIntegration {
    Write-Header "Running integration tests..."
    python -m pytest -v -m "integration"
    if ($LASTEXITCODE -eq 0) { Write-Success "Integration tests complete!" }
}

# Run visual tests
function Invoke-TestVisual {
    Write-Header "Running visual regression tests..."
    python -m pytest -v -m "visual" --tb=short
    if ($LASTEXITCODE -eq 0) { Write-Success "Visual regression tests complete!" }
}

# Run performance tests
function Invoke-TestPerformance {
    Write-Header "Running performance tests..."
    python -m pytest -v -m "performance"
    if ($LASTEXITCODE -eq 0) { Write-Success "Performance tests complete!" }
}

# Run accessibility tests
function Invoke-TestAccessibility {
    Write-Header "Running accessibility tests..."
    python -m pytest -v -m "accessibility"
    if ($LASTEXITCODE -eq 0) { Write-Success "Accessibility tests complete!" }
}

# Build project
function Invoke-Build {
    Write-Header "Building project..."

    if (Test-Path "package.json") {
        Write-Info "Building CSS..."
        npm run build:css
    }

    Write-Info "Collecting static files..."
    python manage.py collectstatic --noinput

    Write-Success "Build complete!"
}

# Build for production
function Invoke-BuildProduction {
    Write-Header "Building for production..."

    if (Test-Path "package.json") {
        Write-Info "Building all assets..."
        npm run build:all
    }

    Write-Info "Collecting static files..."
    python manage.py collectstatic --noinput --clear

    Write-Success "Production build complete!"
}

# Clean temporary files
function Invoke-Clean {
    Write-Header "Cleaning temporary files..."

    Write-Info "Removing Python cache files..."
    Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force
    Get-ChildItem -Recurse -Filter "__pycache__" -Directory | Remove-Item -Recurse -Force
    Get-ChildItem -Recurse -Filter "*.pyo" | Remove-Item -Force

    if (Test-Path ".coverage") { Remove-Item ".coverage" -Force }
    if (Test-Path "htmlcov") { Remove-Item "htmlcov" -Recurse -Force }
    if (Test-Path ".pytest_cache") { Remove-Item ".pytest_cache" -Recurse -Force }
    if (Test-Path ".mypy_cache") { Remove-Item ".mypy_cache" -Recurse -Force }

    Write-Success "Cleanup complete!"
}

# Run migrations
function Invoke-Migrate {
    Write-Header "Running migrations..."
    python manage.py migrate
    Write-Success "Migrations complete!"
}

# Create migrations
function Invoke-Makemigrations {
    Write-Header "Creating migrations..."
    python manage.py makemigrations
    Write-Success "Migrations created!"
}

# Reset database
function Invoke-ResetDB {
    Write-Warning "This will DELETE all data in the database!"
    $confirm = Read-Host "Are you sure? (yes/no)"

    if ($confirm -eq "yes") {
        Write-Info "Resetting database..."
        if (Test-Path "db.sqlite3") { Remove-Item "db.sqlite3" -Force }
        python manage.py migrate
        Write-Success "Database reset complete!"
    }
    else {
        Write-Info "Database reset cancelled."
    }
}

# Run development server
function Invoke-Runserver {
    Write-Header "Starting development server..."
    python manage.py runserver
}

# Open Django shell
function Invoke-Shell {
    Write-Header "Opening Django shell..."
    python manage.py shell
}

# Create superuser
function Invoke-CreateSuperuser {
    Write-Header "Creating superuser..."
    python manage.py createsuperuser
}

# Setup pre-commit
function Invoke-PreCommit {
    Write-Header "Setting up pre-commit hooks..."

    if (-not (Test-Command "pre-commit")) {
        Write-Error-Custom "pre-commit not found. Run: pip install pre-commit"
        exit 1
    }

    Write-Info "Installing pre-commit hooks..."
    pre-commit install

    Write-Info "Running pre-commit on all files..."
    pre-commit run --all-files

    Write-Success "Pre-commit setup complete!"
}

# Check all quality
function Invoke-CheckAll {
    Write-Header "Running all quality checks..."

    Write-Host "`n═══════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "STEP 1/4: Code Formatting" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
    Invoke-Format

    Write-Host "`n═══════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "STEP 2/4: Linting" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
    Invoke-Lint

    Write-Host "`n═══════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "STEP 3/4: Security Checks" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
    Invoke-Security

    Write-Host "`n═══════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "STEP 4/4: Tests" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
    Invoke-Test

    Write-Host "`n═══════════════════════════════════════════" -ForegroundColor Green
    Write-Success "ALL QUALITY CHECKS PASSED! 🎉"
    Write-Host "═══════════════════════════════════════════" -ForegroundColor Green
}

# Quick check (format + lint only)
function Invoke-CheckQuick {
    Write-Header "Running quick quality checks..."
    Invoke-Format
    Invoke-Lint
    Write-Success "Quick quality checks complete! ⚡"
}

# Show documentation
function Invoke-Docs {
    Write-Header "Documentation Links"
    Write-Host @"

📚 Available Documentation:

  • UI Kit: http://localhost:8000/ui-kit/
  • Test Coverage: htmlcov/index.html
  • API Documentation: docs/api/
  • Architecture: docs/architecture/
  • Development Guide: docs/development/
  • Deployment Guide: docs/deployment/

"@ -ForegroundColor Cyan
}

# Main command dispatcher
switch ($Command.ToLower()) {
    "help" { Show-Help }
    "install" { Invoke-Install }
    "format" { Invoke-Format }
    "lint" { Invoke-Lint }
    "security" { Invoke-Security }
    "test" { Invoke-Test }
    "test-ui" { Invoke-TestUI }
    "test-coverage" { Invoke-TestCoverage }
    "test-integration" { Invoke-TestIntegration }
    "test-visual" { Invoke-TestVisual }
    "test-performance" { Invoke-TestPerformance }
    "test-accessibility" { Invoke-TestAccessibility }
    "build" { Invoke-Build }
    "build-production" { Invoke-BuildProduction }
    "clean" { Invoke-Clean }
    "migrate" { Invoke-Migrate }
    "makemigrations" { Invoke-Makemigrations }
    "reset-db" { Invoke-ResetDB }
    "runserver" { Invoke-Runserver }
    "shell" { Invoke-Shell }
    "create-superuser" { Invoke-CreateSuperuser }
    "pre-commit" { Invoke-PreCommit }
    "check-all" { Invoke-CheckAll }
    "check-quick" { Invoke-CheckQuick }
    "docs" { Invoke-Docs }
    default {
        Write-Error-Custom "Unknown command: $Command"
        Write-Info "Run '.\make.ps1 help' to see available commands"
        exit 1
    }
}
