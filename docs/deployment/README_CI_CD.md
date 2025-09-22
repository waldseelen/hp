# CI/CD Pipeline Documentation

## Overview

This project includes a comprehensive CI/CD pipeline using GitHub Actions with automated testing, code quality checks, and security scanning.

## Pipeline Structure

### Main CI Pipeline (`.github/workflows/ci.yml`)

- **Triggers**: Push to main/develop branches, Pull Requests to main
- **Jobs**:
  - **test**: Runs Django tests with coverage
  - **code-quality**: Black, isort, flake8, mypy checks
  - **security**: Bandit and Safety vulnerability scanning
  - **frontend**: JavaScript/CSS linting and testing
  - **lighthouse**: Performance and accessibility testing
  - **build-status**: Overall build status reporting

### Security Pipeline (`.github/workflows/security.yml`)

- **Triggers**: Push, PR, Weekly schedule (Sundays 2 AM UTC)
- **Jobs**:
  - **security-scan**: Bandit + Safety with PR comments
  - **dependency-check**: Trivy vulnerability scanning
  - **secrets-scan**: TruffleHog secrets detection

## Configuration Files

### Code Quality
- `.flake8`: Python linting configuration
- `.bandit`: Security scanning configuration
- `.safety-policy.json`: Vulnerability scanning policy
- `pyproject.toml`: Black, isort, mypy, pytest configuration

### Lighthouse
- `.lighthouserc.json`: Performance/accessibility thresholds

## Current Status

✅ **Completed Setup:**
- GitHub Actions CI/CD pipeline
- Python test runner with pytest
- Code quality checks (Black, isort, flake8)
- Security scanning (Bandit, Safety)
- Lighthouse configuration
- Build status reporting

## Security Scan Results

The current dependency scan identified 10 vulnerabilities:
- 9 in Django 5.1 (various CVEs - upgrade to Django 5.1.11+ recommended)
- 1 in requests 2.32.3 (CVE-2024-47081 - upgrade to 2.32.4+ recommended)

## Next Steps

1. Address dependency vulnerabilities by updating versions
2. Test pipeline on actual commit/PR
3. Add badges to main README
4. Configure notifications/alerts

## Usage

The pipeline runs automatically on:
- Every push to main/develop
- Every pull request to main
- Weekly security scans

Manual trigger: Go to Actions tab in GitHub and run workflows manually.