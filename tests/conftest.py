"""
Configuration for pytest
"""

import os
import django
import pytest
from django.conf import settings


def pytest_configure():
    """
    Configure Django settings for testing.
    This is automatically called by pytest.
    """
    if not settings.configured:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portfolio_site.settings.development')
        
        # Minimal settings for testing
        settings.configure(
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=[
                'django.contrib.admin',
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'django.contrib.sessions',
                'django.contrib.messages',
                'django.contrib.staticfiles',
                'apps.blog',
                'apps.main',
                'apps.tools',
                'apps.contact',
            ],
            MIDDLEWARE=[
                'django.contrib.sessions.middleware.SessionMiddleware',
                'django.middleware.common.CommonMiddleware',
                'django.middleware.csrf.CsrfViewMiddleware',
                'django.contrib.auth.middleware.AuthenticationMiddleware',
                'django.contrib.messages.middleware.MessageMiddleware',
            ],
            SECRET_KEY='test-secret-key-for-pytest',
            STATIC_URL='/static/',
            MEDIA_URL='/media/',
            USE_TZ=True,
            LANGUAGE_CODE='en-us',
            USE_I18N=True,
            USE_L10N=True,
            ROOT_URLCONF='portfolio_site.urls',
            TEMPLATES=[
                {
                    'BACKEND': 'django.template.backends.django.DjangoTemplates',
                    'DIRS': ['templates'],
                    'APP_DIRS': True,
                    'OPTIONS': {
                        'context_processors': [
                            'django.template.context_processors.debug',
                            'django.template.context_processors.request',
                            'django.contrib.auth.context_processors.auth',
                            'django.contrib.messages.context_processors.messages',
                        ],
                    },
                },
            ],
            # Simplified for testing
            CACHES={
                'default': {
                    'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                }
            },
            EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        )
        
        django.setup()


@pytest.fixture(scope='session')
def django_db_setup():
    """Set up the Django database for testing."""
    from django.core.management import call_command
    from django.test.utils import setup_test_environment, teardown_test_environment
    
    setup_test_environment()
    call_command('migrate', '--run-syncdb', verbosity=0)
    
    yield
    
    teardown_test_environment()


@pytest.fixture
def client():
    """Django test client fixture."""
    from django.test import Client
    return Client()


@pytest.fixture
def user():
    """Create a test user."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )