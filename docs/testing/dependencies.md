# Test Dependencies Documentation

**Version:** 1.0
**Last Updated:** 2025-11-01
**Phase:** 22A - Test Infrastructure

---

## 📋 Overview

This document categorizes all project dependencies into **required** (must be installed for tests to run) and **optional** (can be mocked for testing).

---

## ✅ Required Dependencies

These packages **must** be installed for tests to run:

### Core Testing Framework
| Package | Version | Purpose | Installation |
|---------|---------|---------|-------------|
| `pytest` | 8.4.2 | Test framework | `pip install pytest` |
| `pytest-django` | 4.11.1 | Django integration | `pip install pytest-django` |
| `pytest-cov` | 7.0.0 | Coverage reporting | `pip install pytest-cov` |
| `pytest-xdist` | 3.8.0 | Parallel execution | `pip install pytest-xdist` |
| `pytest-mock` | 3.15.1 | Mocking utilities | `pip install pytest-mock` |
| `coverage` | 7.0+ | Coverage measurement | `pip install coverage` |

### Django & Core
| Package | Version | Purpose | Installation |
|---------|---------|---------|-------------|
| `Django` | 5.1 | Web framework | `pip install Django==5.1` |
| `python-decouple` | 3.8+ | Config management | `pip install python-decouple` |
| `Pillow` | 10.0+ | Image processing | `pip install Pillow` |

### DRF (if testing API)
| Package | Version | Purpose | Installation |
|---------|---------|---------|-------------|
| `djangorestframework` | 3.14+ | REST API framework | `pip install djangorestframework` |

### Install All Required
```bash
# Core testing dependencies
pip install pytest pytest-django pytest-cov pytest-xdist pytest-mock coverage

# Django and essentials
pip install Django==5.1 python-decouple Pillow

# API testing (if needed)
pip install djangorestframework
```

---

## 🔧 Optional Dependencies (Can Be Mocked)

These packages are **optional** for testing. Mock implementations are provided in `tests/mocks/`.

### Search Engine
| Package | Version | Purpose | Mock Available | Notes |
|---------|---------|---------|----------------|-------|
| `meilisearch` | 0.30+ | Search engine client | ✅ `MockMeilisearchClient` | See: `tests/mocks/meilisearch_mock.py` |

**Mock Usage:**
```python
from tests.mocks import MockMeilisearchClient

@pytest.fixture
def mock_search(monkeypatch):
    mock_client = MockMeilisearchClient("http://localhost:7700")
    monkeypatch.setattr("meilisearch.Client", lambda *args: mock_client)
    return mock_client

def test_search_functionality(mock_search):
    index = mock_search.index("posts")
    index.add_documents([{"id": 1, "title": "Test"}])
    results = index.search("Test")
    assert len(results["hits"]) == 1
```

### Cache & Queue
| Package | Version | Purpose | Mock Available | Notes |
|---------|---------|---------|----------------|-------|
| `redis` | 5.0+ | Cache/queue backend | ✅ `MockRedisClient` | See: `tests/mocks/redis_mock.py` |
| `django-redis` | 5.4+ | Django Redis integration | ✅ Via MockRedisClient | Uses Django LocMemCache in tests |

**Mock Usage:**
```python
from tests.mocks import MockRedisClient

@pytest.fixture
def mock_redis(monkeypatch):
    mock_client = MockRedisClient()
    monkeypatch.setattr("redis.Redis", lambda *args, **kwargs: mock_client)
    return mock_client

def test_cache_operation(mock_redis):
    mock_redis.set("key", "value", ex=60)
    assert mock_redis.get("key") == b"value"
```

**Note:** Tests use Django's `LocMemCache` by default (configured in `project/settings/testing.py`), so Redis is not required.

### Task Queue
| Package | Version | Purpose | Mock Available | Notes |
|---------|---------|---------|----------------|-------|
| `celery` | 5.3+ | Async task queue | ✅ `MockCeleryApp` | See: `tests/mocks/celery_mock.py` |

**Mock Usage:**
```python
from tests.mocks import MockCeleryApp

@pytest.fixture
def mock_celery(monkeypatch):
    mock_app = MockCeleryApp("test_app")
    monkeypatch.setattr("celery.Celery", lambda *args, **kwargs: mock_app)
    return mock_app

def test_async_task(mock_celery):
    @mock_celery.task
    def add(x, y):
        return x + y

    result = add.delay(2, 3)
    assert result.get() == 5
    assert add.call_count == 1
```

### WebSockets (Chat Feature)
| Package | Version | Purpose | Mock Available | Notes |
|---------|---------|---------|----------------|-------|
| `channels` | 4.0+ | WebSocket support | ⚠️ Partial | Test with `ChannelsLiveServerTestCase` |
| `channels-redis` | 4.2+ | Channels Redis layer | ⚠️ Use InMemoryChannelLayer | See Django Channels docs |

**Test Settings:**
```python
# project/settings/testing.py
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}
```

### Email
| Package | Version | Purpose | Mock Available | Notes |
|---------|---------|---------|----------------|-------|
| Email backend | - | Email sending | ✅ Django `locmem` backend | Configured in testing.py |

**Test Settings:**
```python
# project/settings/testing.py
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Access sent emails in tests
from django.core import mail

def test_email_sent():
    # ... trigger email sending ...
    assert len(mail.outbox) == 1
    assert mail.outbox[0].subject == "Test Subject"
```

### CORS & Security
| Package | Version | Purpose | Mock Available | Notes |
|---------|---------|---------|----------------|-------|
| `django-cors-headers` | 4.3+ | CORS middleware | ❌ Not needed in tests | Middleware disabled in testing.py |

---

## 🚫 Dependencies NOT Required for Tests

These are **never** required for testing:

### Production Server
- `gunicorn` - WSGI server (only for production)
- `uvicorn` - ASGI server (only for production)
- `daphne` - ASGI server (only for production)

### Database Drivers (Production)
- `psycopg2` - PostgreSQL driver (tests use SQLite)
- `mysqlclient` - MySQL driver (tests use SQLite)

### Static File Storage
- `whitenoise` - Static file serving (not needed in tests)
- `boto3` - AWS S3 (not needed in tests)

### Monitoring & APM
- `sentry-sdk` - Error tracking (disabled in tests)
- `newrelic` - APM (disabled in tests)

### CI/CD Tools
- `codecov` - Coverage upload (only in CI)
- `pytest-github-actions-annotate-failures` - CI annotations

---

## 📦 Installation Strategies

### Strategy 1: Minimal Install (Fastest)
```bash
# Only required dependencies
pip install pytest pytest-django pytest-cov pytest-mock
pip install Django==5.1 python-decouple Pillow djangorestframework

# Run tests
pytest
```

**Pros:** Fast installation, minimal dependencies
**Cons:** Some features may be skipped if optional deps are missing

---

### Strategy 2: Full Install (Recommended for Local Dev)
```bash
# Install everything from requirements.txt
pip install -r requirements.txt

# Run tests
pytest
```

**Pros:** All features available, mirrors production environment
**Cons:** Slower installation, requires external services for full functionality

---

### Strategy 3: Test-Only Install (CI/CD)
```bash
# Install from test-specific requirements
pip install -r requirements/test.txt  # If you create this file

# Run tests
pytest --cov=apps --cov-report=xml
```

**Pros:** Optimized for CI, reproducible builds
**Cons:** Need to maintain separate requirements file

---

## 🔍 Dependency Audit Results

### Audit Performed: 2025-11-01

#### ✅ Successfully Mocked
- **Meilisearch:** Full mock implementation with search/index operations
- **Redis:** Complete in-memory key-value store
- **Celery:** Synchronous task execution for tests
- **Email:** Django's locmem backend

#### ⚠️ Partially Mocked
- **Channels:** Use InMemoryChannelLayer (built-in)
- **Database:** Use SQLite in-memory (built-in)
- **Cache:** Use LocMemCache (built-in)

#### ❌ No Mock Needed
- **Static files:** Disabled in tests
- **Media uploads:** Uses temp directory
- **CORS headers:** Middleware disabled
- **Security middleware:** Simplified in tests

---

## 🎯 Testing Without External Services

### Current Test Configuration

The project is configured to run **all tests without any external services**:

#### Database: SQLite In-Memory
```python
# project/settings/testing.py
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "ATOMIC_REQUESTS": True,
    }
}
```

#### Cache: Local Memory
```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-cache",
    }
}
```

#### Email: Local Memory
```python
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
```

#### Channels: In-Memory Layer
```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}
```

### Running Tests Completely Offline

```bash
# No network, no services, just tests
pytest --cov=apps

# All tests run in memory, no external dependencies
```

---

## 🛠️ Mock Usage Guidelines

### When to Use Mocks

✅ **USE MOCKS FOR:**
- External API calls (search engines, payment processors)
- Expensive operations (image processing, video encoding)
- Non-deterministic behavior (random data, timestamps)
- Network-dependent services (Redis, S3, external APIs)
- Async operations you want to test synchronously

❌ **DON'T MOCK:**
- Django ORM (use test database instead)
- Simple utility functions
- Django views (test with TestClient)
- Template rendering
- Your own business logic

### Mock Best Practices

1. **Mock at the right level:**
   ```python
   # Good: Mock the external library
   monkeypatch.setattr("meilisearch.Client", MockMeilisearchClient)

   # Bad: Mock your own function
   monkeypatch.setattr("apps.main.search.perform_search", lambda: [])
   ```

2. **Use fixtures for reusable mocks:**
   ```python
   @pytest.fixture
   def mock_search(monkeypatch):
       mock = MockMeilisearchClient("http://test")
       monkeypatch.setattr("meilisearch.Client", lambda *a: mock)
       return mock
   ```

3. **Verify mock interactions:**
   ```python
   def test_search_called(mock_search):
       # ... perform search ...
       index = mock_search.index("posts")
       assert len(index.documents) > 0
   ```

---

## 📚 Related Documentation

- [Test Infrastructure Guide](./test-infrastructure.md) - How to write and run tests
- [Coverage Baseline Report](./coverage-baseline.md) - Current coverage metrics
- [Mock API Reference](../mocks/README.md) - Detailed mock class documentation

---

## 🔄 Keeping This Document Updated

### When to Update

Update this document when:
- ✅ Adding a new external dependency
- ✅ Creating a new mock implementation
- ✅ Changing test configuration
- ✅ Discovering a dependency can be mocked
- ✅ Removing a deprecated dependency

### Update Process

1. Update the relevant section
2. Test that mocks work correctly
3. Update version numbers
4. Add usage examples
5. Commit with message: `docs: Update test dependencies [Phase 22A.3]`

---

**Document Version:** 1.0
**Last Audit:** 2025-11-01 (Phase 22A.3)
**Status:** ✅ Complete - All optional dependencies mocked
**Next Review:** After Phase 22B (when adding more tests)
