# Linting Configuration Guide

This document outlines the linting and code quality tools configured for this Django project.

## Tools Overview

### Flake8
- **Purpose**: Python code style and error checking
- **Configuration**: `.flake8` and `pyproject.toml`
- **Rules**:
  - Max line length: 88 characters (Black compatible)
  - Excludes: migrations, venv, node_modules, staticfiles, etc.
  - Ignores: E203, E501, W503, F401 (handled by other tools)
  - Per-file ignores for Django-specific files

### Black
- **Purpose**: Python code formatting
- **Configuration**: `pyproject.toml`
- **Settings**:
  - Line length: 88
  - Target Python version: 3.11
  - Excludes standard directories

### isort
- **Purpose**: Import sorting
- **Configuration**: `pyproject.toml`
- **Settings**:
  - Profile: Black compatible
  - Known Django modules
  - Sections: FUTURE, STDLIB, DJANGO, THIRDPARTY, FIRSTPARTY, LOCALFOLDER

### mypy
- **Purpose**: Static type checking
- **Configuration**: `pyproject.toml`
- **Settings**:
  - Python version: 3.11
  - Ignores missing imports for Django/third-party
  - Excludes standard directories

### Bandit
- **Purpose**: Security vulnerability scanning
- **Configuration**: `.bandit`
- **Settings**:
  - Excludes test and build directories
  - Skips Django-specific false positives
  - High confidence, medium severity minimum

## Running Linters

### Individual Tools
```bash
# Flake8
flake8 .

# Black (check only)
black --check .

# Black (format)
black .

# isort (check only)
isort --check-only .

# isort (fix)
isort .

# mypy
mypy .

# Bandit
bandit -r apps/
```

### Combined Commands (Makefile)
```bash
# Check all
make lint

# Format all
make format

# Security check
make security

# Run all quality checks
make check-all
```

## Common Issues and Solutions

### Flake8 Errors
- **E501 Line too long**: Use Black to format automatically
- **F401 Imported but unused**: Remove unused imports or add to per-file-ignores
- **E203 Whitespace before ':'**: Ignored (Black compatibility)

### mypy Issues
- **Missing imports**: Add to overrides in pyproject.toml
- **Django stubs**: Install django-stubs if needed
- **Dynamic imports**: Use TYPE_CHECKING blocks

### Bandit False Positives
- **B101 assert_used**: OK in Django tests
- **B601-B607 subprocess**: Review carefully, skip if safe

## Pre-commit Hooks

Pre-commit hooks are configured to run automatically on commit:

- black
- isort
- flake8
- mypy (if configured)
- bandit (if configured)

## CI/CD Integration

GitHub Actions runs:
- Flake8
- mypy
- Bandit
- Test coverage (85% minimum)

## File Structure

```
.flake8          # Flake8 configuration
.bandit          # Bandit security configuration
pyproject.toml   # Black, isort, mypy, pytest, coverage config
Makefile         # Quality check commands
.pre-commit-config.yaml  # Pre-commit hooks
```

## Maintenance

- Update tool versions quarterly
- Review and update ignore lists as needed
- Monitor CI/CD for new failures
- Document any project-specific rules
