# Test Infrastructure Guide

**Version:** 1.0
**Last Updated:** 2025
**Maintainer:** Development Team

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Test Environment Setup](#test-environment-setup)
4. [Running Tests](#running-tests)
5. [Writing Tests](#writing-tests)
6. [Fixtures Reference](#fixtures-reference)
7. [Coverage Reporting](#coverage-reporting)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)
10. [CI/CD Integration](#cicd-integration)

---

## 🎯 Overview

### Infrastructure Components

| Component | Purpose | Status |
|-----------|---------|--------|
| **pytest** | Test framework | ✅ Configured |
| **pytest-django** | Django integration | ✅ Configured |
| **pytest-cov** | Coverage reporting | ✅ Configured |
| **pytest-xdist** | Parallel execution | ✅ Configured |
| **pytest-mock** | Mocking utilities | ✅ Configured |
| **Coverage.py** | Coverage measurement | ✅ Configured |

### Architecture

```
tests/
├── conftest.py           # Global fixtures & configuration
├── unit/                 # Unit tests (models, forms, utils)
│   ├── test_models.py
│   ├── test_views.py
│   └── test_forms.py
├── integration/          # Integration tests (views + templates)
│   ├── test_contact_flow.py
│   └── test_search_flow.py
└── e2e/                  # End-to-end tests (full workflows)
    └── test_user_journey.py
```

---

## ⚡ Quick Start

### 1. Install Dependencies

```bash
# Already installed in .venv-1
pip install pytest pytest-django pytest-cov pytest-xdist pytest-mock
```

### 2. Run All Tests

```bash
# Run all tests with coverage
pytest --cov=apps --cov-report=html

# Run specific test file
pytest tests/unit/test_models.py

# Run with verbose output
pytest -v

# Run in parallel (4 workers)
pytest -n 4
```

### 3. View Coverage Report

```bash
# Open HTML coverage report
start htmlcov/index.html  # Windows
open htmlcov/index.html   # macOS
xdg-open htmlcov/index.html  # Linux
```

---

## 🔧 Test Environment Setup

### Configuration Files

#### `pytest.ini`
```ini
[pytest]
DJANGO_SETTINGS_MODULE = portfolio_site.settings.test
python_files = test_*.py
python_classes = Test* *Tests *TestCase
python_functions = test_*
testpaths = tests/
addopts =
    --reuse-db
    --nomigrations
    --strict-markers
    --tb=short
markers =
    slow: marks tests as slow
    search: tests related to search functionality
    cache: tests related to caching
    database: tests that require database access
    auth: tests related to authentication
    email: tests that send emails
```

#### `project/settings/testing.py`

Key features:
- **Database:** SQLite in-memory (`:memory:`)
- **Migrations:** Disabled via `DisableMigrations` class
- **Cache:** LocMemCache (in-memory)
- **Email:** `locmem` backend (captured in memory)
- **Password Hashing:** MD5 (fast for testing)
- **Logging:** Disabled (NullHandler)

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "ATOMIC_REQUESTS": True,
    }
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

MIGRATION_MODULES = DisableMigrations()
```

#### `tests/conftest.py`

Global fixtures available to all tests:

```python
import os
import django

# Setup Django before any imports
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "portfolio_site.settings.test")
django.setup()

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from rest_framework.test import APIClient

User = get_user_model()

@pytest.fixture
def user(db):
    """Create a regular test user"""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
    )

@pytest.fixture
def admin_user(db):
    """Create an admin test user"""
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpass123",
    )

@pytest.fixture
def client():
    """Django test client"""
    return Client()

@pytest.fixture
def api_client():
    """DRF API test client"""
    return APIClient()

@pytest.fixture
def authenticated_client(client, user):
    """Pre-authenticated Django client"""
    client.force_login(user)
    return client

@pytest.fixture
def authenticated_api_client(api_client, user):
    """Pre-authenticated API client"""
    api_client.force_authenticate(user=user)
    return api_client
```

---

## 🏃 Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_models.py

# Run specific test class
pytest tests/unit/test_models.py::ProjectModelTests

# Run specific test method
pytest tests/unit/test_models.py::ProjectModelTests::test_project_creation

# Run tests matching pattern
pytest -k "model"  # Runs all tests with "model" in name
pytest -k "test_user or test_admin"

# Run marked tests
pytest -m "search"  # Only search-related tests
pytest -m "not slow"  # Exclude slow tests
```

### Verbose & Debug Options

```bash
# Verbose output
pytest -v

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Show local variables on failure
pytest -l

# Run last failed tests only
pytest --lf

# Run failed tests first, then others
pytest --ff
```

### Parallel Execution

```bash
# Run with 4 workers
pytest -n 4

# Auto-detect CPU count
pytest -n auto

# Distribute tests by file
pytest --dist loadfile
```

### Coverage Options

```bash
# Basic coverage report
pytest --cov=apps

# HTML report
pytest --cov=apps --cov-report=html

# XML report (for CI/CD)
pytest --cov=apps --cov-report=xml

# Terminal report with missing lines
pytest --cov=apps --cov-report=term-missing

# Multiple reports
pytest --cov=apps --cov-report=html --cov-report=xml --cov-report=term
```

---

## ✍️ Writing Tests

### Test File Structure

```python
"""
tests/unit/test_models.py

Unit tests for Django models
"""
import pytest
from django.contrib.auth import get_user_model
from apps.blog.models import Post, Category

User = get_user_model()


class TestCategoryModel:
    """Tests for Category model"""

    @pytest.mark.django_db
    def test_category_creation(self):
        """Test creating a category"""
        category = Category.objects.create(
            name="Technology",
            slug="technology"
        )
        assert category.name == "Technology"
        assert str(category) == "Technology"

    @pytest.mark.django_db
    def test_category_slug_unique(self):
        """Test category slug uniqueness"""
        Category.objects.create(name="Tech", slug="tech")

        with pytest.raises(Exception):  # IntegrityError
            Category.objects.create(name="Tech 2", slug="tech")


class TestPostModel:
    """Tests for Post model"""

    @pytest.fixture
    def category(self, db):
        """Create a test category"""
        return Category.objects.create(
            name="Technology",
            slug="technology"
        )

    @pytest.fixture
    def author(self, db):
        """Create a test author"""
        return User.objects.create_user(
            username="author",
            email="author@example.com",
            password="pass123"
        )

    @pytest.mark.django_db
    def test_post_creation(self, author, category):
        """Test creating a blog post"""
        post = Post.objects.create(
            title="Test Post",
            slug="test-post",
            content="Test content",
            author=author,
            category=category,
            status="published"
        )
        assert post.title == "Test Post"
        assert post.author == author
        assert post.is_published() is True

    @pytest.mark.django_db
    def test_draft_post_not_visible(self, author, category):
        """Test draft posts are not publicly visible"""
        post = Post.objects.create(
            title="Draft Post",
            slug="draft-post",
            content="Draft content",
            author=author,
            category=category,
            status="draft"
        )
        assert post.is_published() is False

        # Query published posts
        published = Post.objects.filter(status="published")
        assert post not in published
```

### View Testing Examples

```python
"""
tests/unit/test_views.py

Unit tests for Django views
"""
import pytest
from django.urls import reverse
from apps.blog.models import Post, Category


@pytest.mark.django_db
class TestBlogViews:
    """Tests for blog views"""

    @pytest.fixture
    def published_post(self, user):
        """Create a published test post"""
        category = Category.objects.create(name="Tech", slug="tech")
        return Post.objects.create(
            title="Published Post",
            slug="published-post",
            content="Content",
            author=user,
            category=category,
            status="published"
        )

    def test_post_list_view(self, client, published_post):
        """Test blog post list view"""
        url = reverse("blog:post_list")
        response = client.get(url)

        assert response.status_code == 200
        assert "Published Post" in response.content.decode()
        assert published_post in response.context["posts"]

    def test_post_detail_view(self, client, published_post):
        """Test blog post detail view"""
        url = reverse("blog:post_detail", kwargs={"slug": published_post.slug})
        response = client.get(url)

        assert response.status_code == 200
        assert published_post.title in response.content.decode()
        assert response.context["post"] == published_post

    def test_draft_post_not_accessible(self, client, user):
        """Test draft posts return 404"""
        category = Category.objects.create(name="Tech", slug="tech")
        draft_post = Post.objects.create(
            title="Draft",
            slug="draft",
            content="Content",
            author=user,
            category=category,
            status="draft"
        )

        url = reverse("blog:post_detail", kwargs={"slug": draft_post.slug})
        response = client.get(url)

        assert response.status_code == 404

    def test_authenticated_user_can_create_post(self, authenticated_client):
        """Test authenticated user can create post"""
        category = Category.objects.create(name="Tech", slug="tech")
        url = reverse("blog:post_create")

        data = {
            "title": "New Post",
            "slug": "new-post",
            "content": "New content",
            "category": category.id,
            "status": "draft"
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == 302  # Redirect after success
        assert Post.objects.filter(slug="new-post").exists()
```

### API Testing Examples

```python
"""
tests/unit/test_api.py

Unit tests for REST API endpoints
"""
import pytest
from django.urls import reverse
from rest_framework import status
from apps.blog.models import Post, Category


@pytest.mark.django_db
class TestBlogAPI:
    """Tests for blog API endpoints"""

    @pytest.fixture
    def category(self):
        return Category.objects.create(name="Tech", slug="tech")

    @pytest.fixture
    def published_post(self, user, category):
        return Post.objects.create(
            title="API Post",
            slug="api-post",
            content="API content",
            author=user,
            category=category,
            status="published"
        )

    def test_post_list_api(self, api_client, published_post):
        """Test GET /api/posts/"""
        url = reverse("api:post-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["title"] == "API Post"

    def test_post_detail_api(self, api_client, published_post):
        """Test GET /api/posts/{id}/"""
        url = reverse("api:post-detail", kwargs={"pk": published_post.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == published_post.title
        assert response.data["slug"] == published_post.slug

    def test_create_post_requires_auth(self, api_client, category):
        """Test POST /api/posts/ requires authentication"""
        url = reverse("api:post-list")
        data = {
            "title": "New Post",
            "slug": "new-post",
            "content": "Content",
            "category": category.id
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authenticated_user_can_create_post(
        self, authenticated_api_client, category
    ):
        """Test authenticated user can create post via API"""
        url = reverse("api:post-list")
        data = {
            "title": "Auth Post",
            "slug": "auth-post",
            "content": "Auth content",
            "category": category.id,
            "status": "draft"
        }

        response = authenticated_api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert Post.objects.filter(slug="auth-post").exists()
```

---

## 🎁 Fixtures Reference

### Built-in Fixtures (from conftest.py)

#### `user(db)` - Regular Test User
```python
def test_user_fixture(user):
    """Example using user fixture"""
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.check_password("testpass123")
```

#### `admin_user(db)` - Admin User
```python
def test_admin_fixture(admin_user):
    """Example using admin_user fixture"""
    assert admin_user.is_staff
    assert admin_user.is_superuser
```

#### `client` - Django Test Client
```python
def test_client_fixture(client):
    """Example using client fixture"""
    response = client.get("/")
    assert response.status_code == 200
```

#### `api_client` - DRF API Client
```python
def test_api_client_fixture(api_client):
    """Example using api_client fixture"""
    response = api_client.get("/api/posts/")
    assert response.status_code == 200
```

#### `authenticated_client` - Pre-Authenticated Client
```python
def test_authenticated_client(authenticated_client):
    """Example using authenticated_client"""
    response = authenticated_client.get("/profile/")
    # No need to login manually!
    assert response.status_code == 200
```

#### `authenticated_api_client` - Pre-Authenticated API Client
```python
def test_authenticated_api(authenticated_api_client):
    """Example using authenticated_api_client"""
    response = authenticated_api_client.post("/api/posts/", data={...})
    # Already authenticated!
    assert response.status_code == 201
```

### Custom Fixtures

Create test-specific fixtures in your test files:

```python
@pytest.fixture
def blog_category(db):
    """Create a test blog category"""
    from apps.blog.models import Category
    return Category.objects.create(name="Tech", slug="tech")

@pytest.fixture
def published_post(db, user, blog_category):
    """Create a published test post"""
    from apps.blog.models import Post
    return Post.objects.create(
        title="Test Post",
        slug="test-post",
        content="Content",
        author=user,
        category=blog_category,
        status="published"
    )

# Use in tests
def test_something(published_post):
    assert published_post.status == "published"
```

---

## 📊 Coverage Reporting

### Generating Reports

```bash
# HTML report (browse in browser)
pytest --cov=apps --cov-report=html
start htmlcov/index.html

# Terminal report with missing lines
pytest --cov=apps --cov-report=term-missing

# JSON report (for programmatic analysis)
pytest --cov=apps --cov-report=json

# XML report (for CI/CD tools like Jenkins, GitLab CI)
pytest --cov=apps --cov-report=xml
```

### Understanding Coverage Output

```
Name                              Stmts   Miss  Cover   Missing
---------------------------------------------------------------
apps/blog/models.py                 101     54    47%   20, 26, 41-59
apps/blog/views.py                   30     12    60%   14-22, 25-27
apps/contact/forms.py                80     62    22%   55-87, 91-115
---------------------------------------------------------------
TOTAL                             17841  15980    10%
```

- **Stmts:** Total statements in file
- **Miss:** Uncovered statements
- **Cover:** Coverage percentage
- **Missing:** Line numbers not covered

### Coverage Configuration

Edit `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["apps"]
omit = [
    "*/migrations/*",
    "*/tests/*",
    "*/__pycache__/*",
    "*/venv/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "class .*\\bProtocol\\):",
]
```

---

## ✅ Best Practices

### 1. Test Organization

```
✅ DO: Group related tests in classes
✅ DO: Use descriptive test names
✅ DO: One assertion concept per test
✅ DO: Use fixtures for common setup

❌ DON'T: Put all tests in one file
❌ DON'T: Use generic test names like test_1()
❌ DON'T: Test multiple unrelated things in one test
```

### 2. Test Naming

```python
✅ GOOD:
def test_user_can_login_with_valid_credentials()
def test_contact_form_rejects_invalid_email()
def test_blog_post_slug_auto_generated_from_title()

❌ BAD:
def test_login()
def test_form()
def test_model()
```

### 3. Fixture Usage

```python
✅ GOOD: Use fixtures for reusable test data
@pytest.fixture
def valid_user_data():
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "secure123"
    }

def test_user_creation(valid_user_data):
    user = User.objects.create_user(**valid_user_data)
    assert user.username == valid_user_data["username"]

❌ BAD: Duplicate setup code in every test
def test_user_creation():
    data = {"username": "testuser", ...}  # Repeated everywhere!
    user = User.objects.create_user(**data)
```

### 4. Database Markers

```python
✅ GOOD: Use @pytest.mark.django_db when accessing database
@pytest.mark.django_db
def test_user_creation():
    user = User.objects.create_user(username="test")
    assert User.objects.count() == 1

❌ BAD: Forget marker, get cryptic error
def test_user_creation():  # Will fail!
    user = User.objects.create_user(username="test")
```

### 5. Test Independence

```python
✅ GOOD: Each test is independent
@pytest.mark.django_db
class TestBlogPost:
    def test_create_post(self):
        post = Post.objects.create(title="Test")
        assert Post.objects.count() == 1

    def test_update_post(self):
        post = Post.objects.create(title="Test")
        post.title = "Updated"
        post.save()
        assert Post.objects.first().title == "Updated"

❌ BAD: Tests depend on each other
class TestBlogPost:
    def test_1_create(self):
        self.post = Post.objects.create(title="Test")  # Shared state!

    def test_2_update(self):
        self.post.title = "Updated"  # Depends on test_1!
```

---

## 🔍 Troubleshooting

### Common Issues

#### 1. `Apps aren't loaded yet`
**Error:**
```
django.core.exceptions.AppRegistryNotReady: Apps aren't loaded yet.
```

**Solution:**
Add to top of `conftest.py`:
```python
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "portfolio_site.settings.test")
django.setup()
```

#### 2. `Database access not allowed`
**Error:**
```
RuntimeError: Database access not allowed, use the "django_db" mark
```

**Solution:**
Add `@pytest.mark.django_db` to your test:
```python
@pytest.mark.django_db
def test_something():
    User.objects.create_user(...)
```

#### 3. `No module named 'apps'`
**Error:**
```
ModuleNotFoundError: No module named 'apps.blog'
```

**Solution:**
Ensure `INSTALLED_APPS` in `testing.py` includes your app:
```python
INSTALLED_APPS = [
    ...
    "apps.blog",  # Add this!
]
```

#### 4. Tests are slow
**Problem:** Tests take too long to run

**Solutions:**
```bash
# 1. Run in parallel
pytest -n auto

# 2. Reuse database
pytest --reuse-db

# 3. Skip migrations
pytest --nomigrations

# 4. Run specific tests only
pytest tests/unit/

# 5. Use fast password hasher (already in testing.py)
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
```

#### 5. Coverage doesn't match
**Problem:** Coverage report shows 0% for some files

**Solution:**
Ensure tests actually import and execute code:
```python
# This doesn't improve coverage:
def test_import():
    from apps.blog import models  # Just importing!

# This does:
def test_model_creation():
    from apps.blog.models import Post
    post = Post(title="Test")  # Actually using the code!
    assert post.title == "Test"
```

---

## 🚀 CI/CD Integration

### GitHub Actions Example

`.github/workflows/tests.yml`:
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.14'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-django pytest-cov

    - name: Run tests
      run: |
        pytest --cov=apps --cov-report=xml --cov-report=term

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
```

### GitLab CI Example

`.gitlab-ci.yml`:
```yaml
test:
  image: python:3.14
  before_script:
    - pip install -r requirements.txt
    - pip install pytest pytest-django pytest-cov
  script:
    - pytest --cov=apps --cov-report=xml --cov-report=term
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

---

## 📚 Additional Resources

### Documentation
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-django Documentation](https://pytest-django.readthedocs.io/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Django Testing Documentation](https://docs.djangoproject.com/en/stable/topics/testing/)

### Related Project Docs
- [Coverage Baseline Report](./coverage-baseline.md)
- [Phase 22 Roadmap](../../roadmap.txt)
- [Development Guide](../development/README.md)

---

**Document Version:** 1.0
**Last Updated:** Phase 22A Task 22A.2
**Status:** ✅ Complete and Production Ready
