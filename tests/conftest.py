"""
Configuration for pytest
Provides fixtures and configuration for Django testing
"""

import os

import django

import pytest

# Set Django settings module for testing BEFORE any Django imports
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings.simple")

# Setup Django
django.setup()

# Now we can import Django modules
from django.contrib.auth import get_user_model  # noqa: E402
from django.test import Client  # noqa: E402
from django.utils import timezone  # noqa: E402


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """
    Set up the Django database for testing.
    Uses pytest-django's django_db_setup and creates initial test data.
    """
    with django_db_blocker.unblock():
        # Database is already set up by pytest-django
        # We can add any additional setup here if needed
        pass


@pytest.fixture
def client():
    """Django test client fixture."""
    # Use raise_request_exception=False to avoid template rendering issues
    # with Python 3.14 compatibility
    return Client(raise_request_exception=False)


@pytest.fixture
def api_client():
    """Django REST framework API client fixture."""
    try:
        from rest_framework.test import APIClient

        return APIClient()
    except ImportError:
        # If DRF is not installed, return None
        return None


@pytest.fixture
def user(db):
    """Create a test user."""
    User = get_user_model()
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def admin_user(db):
    """Create a test admin user."""
    User = get_user_model()
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpass123",
    )


@pytest.fixture
def authenticated_client(client, user):
    """Django test client with authenticated user."""
    client.force_login(user)
    return client


@pytest.fixture
def authenticated_api_client(api_client, user):
    """API client with authenticated user."""
    api_client.force_authenticate(user=user)
    return api_client
