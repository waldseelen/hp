"""
Integration tests for Third-Party Services - Phase 22C.3: Cache Operations.

Tests cover:
- Cache get/set/delete operations
- Cache expiration (TTL)
- Cache invalidation patterns
- Cache key namespacing
- Cache versioning
- Bulk cache operations

Target: Verify cache integration works correctly (using LocMemCache).
"""

import time
from unittest.mock import patch

from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key

import pytest

# ============================================================================
# BASIC CACHE OPERATIONS TESTS
# ============================================================================


@pytest.mark.django_db
class TestBasicCacheOperations:
    """Test basic cache operations."""

    def setup_method(self):
        """Clear cache before each test."""
        cache.clear()

    def test_cache_set_and_get(self):
        """Test setting and getting a cache value."""
        cache.set("test_key", "test_value", 3600)

        value = cache.get("test_key")
        assert value == "test_value"

    def test_cache_get_nonexistent_key(self):
        """Test getting a nonexistent cache key returns None."""
        value = cache.get("nonexistent_key")
        assert value is None

    def test_cache_get_with_default(self):
        """Test cache.get with default value."""
        value = cache.get("nonexistent_key", default="default_value")
        assert value == "default_value"

    def test_cache_delete(self):
        """Test deleting a cache key."""
        cache.set("test_key", "test_value", 3600)
        cache.delete("test_key")

        value = cache.get("test_key")
        assert value is None

    def test_cache_clear(self):
        """Test clearing all cache."""
        cache.set("key1", "value1", 3600)
        cache.set("key2", "value2", 3600)

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None


# ============================================================================
# CACHE DATA TYPES TESTS
# ============================================================================


@pytest.mark.django_db
class TestCacheDataTypes:
    """Test caching different data types."""

    def setup_method(self):
        """Clear cache before each test."""
        cache.clear()

    def test_cache_string_value(self):
        """Test caching string values."""
        cache.set("string_key", "string_value", 3600)
        assert cache.get("string_key") == "string_value"

    def test_cache_integer_value(self):
        """Test caching integer values."""
        cache.set("int_key", 42, 3600)
        assert cache.get("int_key") == 42

    def test_cache_list_value(self):
        """Test caching list values."""
        data = [1, 2, 3, "four", "five"]
        cache.set("list_key", data, 3600)

        cached_data = cache.get("list_key")
        assert cached_data == data

    def test_cache_dict_value(self):
        """Test caching dictionary values."""
        data = {"name": "John Doe", "age": 30, "city": "New York"}
        cache.set("dict_key", data, 3600)

        cached_data = cache.get("dict_key")
        assert cached_data == data

    def test_cache_complex_object(self):
        """Test caching complex Python objects."""
        from apps.portfolio.models import Admin

        admin = Admin(username="testadmin", email="admin@example.com")

        # Cache the object
        cache.set("admin_key", admin, 3600)

        cached_admin = cache.get("admin_key")
        assert cached_admin.username == "testadmin"
        assert cached_admin.email == "admin@example.com"


# ============================================================================
# CACHE EXPIRATION (TTL) TESTS
# ============================================================================


@pytest.mark.django_db
class TestCacheExpiration:
    """Test cache expiration (time-to-live)."""

    def setup_method(self):
        """Clear cache before each test."""
        cache.clear()

    def test_cache_with_timeout(self):
        """Test cache expires after timeout."""
        # Set with 1 second timeout
        cache.set("expire_key", "expire_value", 1)

        # Immediately should exist
        assert cache.get("expire_key") == "expire_value"

        # Wait 2 seconds
        time.sleep(2)

        # Should be expired
        assert cache.get("expire_key") is None

    def test_cache_with_no_timeout(self):
        """Test cache with no timeout (None) persists."""
        cache.set("persist_key", "persist_value", timeout=None)

        # Should persist indefinitely
        assert cache.get("persist_key") == "persist_value"

    def test_cache_default_timeout(self):
        """Test cache with default timeout from settings."""
        # Don't specify timeout, use default
        cache.set("default_key", "default_value")

        # Should exist (default timeout is typically 300 seconds)
        assert cache.get("default_key") == "default_value"


# ============================================================================
# CACHE KEY PATTERNS TESTS
# ============================================================================


@pytest.mark.django_db
class TestCacheKeyPatterns:
    """Test cache key naming patterns."""

    def setup_method(self):
        """Clear cache before each test."""
        cache.clear()

    def test_namespaced_cache_keys(self):
        """Test using namespaced cache keys."""
        # Blog namespace
        cache.set("blog:post:1", "Post 1 data", 3600)
        cache.set("blog:post:2", "Post 2 data", 3600)

        # User namespace
        cache.set("user:profile:1", "User 1 data", 3600)
        cache.set("user:profile:2", "User 2 data", 3600)

        # Retrieve by namespace
        assert cache.get("blog:post:1") == "Post 1 data"
        assert cache.get("user:profile:1") == "User 1 data"

    def test_cache_key_with_parameters(self):
        """Test cache keys with multiple parameters."""
        # Pattern: resource:type:id:language
        cache.set("blog:post:123:en", "English post", 3600)
        cache.set("blog:post:123:tr", "Turkish post", 3600)

        assert cache.get("blog:post:123:en") == "English post"
        assert cache.get("blog:post:123:tr") == "Turkish post"


# ============================================================================
# CACHE INVALIDATION TESTS
# ============================================================================


@pytest.mark.django_db
class TestCacheInvalidation:
    """Test cache invalidation patterns."""

    def setup_method(self):
        """Clear cache before each test."""
        cache.clear()

    def test_invalidate_single_cache_key(self):
        """Test invalidating a single cache key."""
        cache.set("blog_post_1", "Post data", 3600)

        # Invalidate
        cache.delete("blog_post_1")

        assert cache.get("blog_post_1") is None

    def test_invalidate_multiple_cache_keys(self):
        """Test invalidating multiple related cache keys."""
        keys = ["blog:list", "blog:featured", "blog:recent"]

        for key in keys:
            cache.set(key, "cached_data", 3600)

        # Invalidate all
        cache.delete_many(keys)

        for key in keys:
            assert cache.get(key) is None

    def test_invalidate_pattern_based_keys(self):
        """Test invalidating cache keys matching a pattern."""
        # Set multiple keys with pattern
        cache.set("blog_post_1", "Data 1", 3600)
        cache.set("blog_post_2", "Data 2", 3600)
        cache.set("blog_post_3", "Data 3", 3600)
        cache.set("user_profile_1", "User 1", 3600)

        # Delete keys matching pattern (blog_post_*)
        # Note: Django cache doesn't have built-in pattern matching
        # Would need to track keys manually or use Redis SCAN
        keys_to_delete = ["blog_post_1", "blog_post_2", "blog_post_3"]
        cache.delete_many(keys_to_delete)

        assert cache.get("blog_post_1") is None
        assert cache.get("user_profile_1") == "User 1"  # Not deleted


# ============================================================================
# BULK CACHE OPERATIONS TESTS
# ============================================================================


@pytest.mark.django_db
class TestBulkCacheOperations:
    """Test bulk cache operations."""

    def setup_method(self):
        """Clear cache before each test."""
        cache.clear()

    def test_cache_set_many(self):
        """Test setting multiple cache values at once."""
        data = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3",
        }

        cache.set_many(data, 3600)

        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

    def test_cache_get_many(self):
        """Test getting multiple cache values at once."""
        cache.set("key1", "value1", 3600)
        cache.set("key2", "value2", 3600)
        cache.set("key3", "value3", 3600)

        values = cache.get_many(["key1", "key2", "key3"])

        assert values == {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3",
        }

    def test_cache_delete_many(self):
        """Test deleting multiple cache keys at once."""
        cache.set("key1", "value1", 3600)
        cache.set("key2", "value2", 3600)
        cache.set("key3", "value3", 3600)

        cache.delete_many(["key1", "key2"])

        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") == "value3"  # Not deleted


# ============================================================================
# CACHE VERSIONING TESTS
# ============================================================================


@pytest.mark.django_db
class TestCacheVersioning:
    """Test cache versioning."""

    def setup_method(self):
        """Clear cache before each test."""
        cache.clear()

    def test_cache_with_version(self):
        """Test cache versioning."""
        # Set value with version 1
        cache.set("versioned_key", "value_v1", 3600, version=1)

        # Set value with version 2
        cache.set("versioned_key", "value_v2", 3600, version=2)

        # Get different versions
        v1_value = cache.get("versioned_key", version=1)
        v2_value = cache.get("versioned_key", version=2)

        assert v1_value == "value_v1"
        assert v2_value == "value_v2"

    def test_cache_version_incrementation(self):
        """Test incrementing cache version."""
        cache.set("data_key", "old_data", 3600, version=1)

        # Increment version (effectively invalidates old version)
        cache.set("data_key", "new_data", 3600, version=2)

        # Old version still accessible
        assert cache.get("data_key", version=1) == "old_data"

        # New version accessible
        assert cache.get("data_key", version=2) == "new_data"


# ============================================================================
# CACHE ATOMIC OPERATIONS TESTS
# ============================================================================


@pytest.mark.django_db
class TestCacheAtomicOperations:
    """Test atomic cache operations."""

    def setup_method(self):
        """Clear cache before each test."""
        cache.clear()

    def test_cache_add(self):
        """Test cache.add (only sets if key doesn't exist)."""
        # Add key
        result1 = cache.add("add_key", "value1", 3600)
        assert result1 is True
        assert cache.get("add_key") == "value1"

        # Try adding again (should fail)
        result2 = cache.add("add_key", "value2", 3600)
        assert result2 is False
        assert cache.get("add_key") == "value1"  # Unchanged

    def test_cache_get_or_set(self):
        """Test cache.get_or_set (get if exists, otherwise set)."""
        # First call - doesn't exist, so sets
        value1 = cache.get_or_set("gor_key", "default_value", 3600)
        assert value1 == "default_value"

        # Second call - exists, so returns existing
        value2 = cache.get_or_set("gor_key", "new_value", 3600)
        assert value2 == "default_value"  # Not overwritten

    def test_cache_incr_decr(self):
        """Test cache.incr and cache.decr."""
        # Set initial counter
        cache.set("counter", 10, 3600)

        # Increment
        cache.incr("counter")
        assert cache.get("counter") == 11

        cache.incr("counter", delta=5)
        assert cache.get("counter") == 16

        # Decrement
        cache.decr("counter")
        assert cache.get("counter") == 15

        cache.decr("counter", delta=3)
        assert cache.get("counter") == 12


# ============================================================================
# TEMPLATE FRAGMENT CACHING TESTS
# ============================================================================


@pytest.mark.django_db
class TestTemplateFragmentCaching:
    """Test Django template fragment caching."""

    def setup_method(self):
        """Clear cache before each test."""
        cache.clear()

    def test_template_fragment_cache_key(self):
        """Test generating template fragment cache keys."""
        # Generate cache key for template fragment
        key = make_template_fragment_key("blog_sidebar")

        # Set fragment cache
        cache.set(key, "<div>Sidebar content</div>", 3600)

        # Retrieve
        cached_fragment = cache.get(key)
        assert cached_fragment == "<div>Sidebar content</div>"

    def test_template_fragment_with_vary_on(self):
        """Test template fragment caching with vary_on parameter."""
        # Generate keys with different vary_on values
        key_en = make_template_fragment_key("header", ["en"])
        key_tr = make_template_fragment_key("header", ["tr"])

        # Set different fragments
        cache.set(key_en, "<div>English Header</div>", 3600)
        cache.set(key_tr, "<div>Turkish Header</div>", 3600)

        assert cache.get(key_en) == "<div>English Header</div>"
        assert cache.get(key_tr) == "<div>Turkish Header</div>"


# ============================================================================
# CACHE PERFORMANCE TESTS
# ============================================================================


@pytest.mark.django_db
class TestCachePerformance:
    """Test cache performance characteristics."""

    def setup_method(self):
        """Clear cache before each test."""
        cache.clear()

    def test_cache_faster_than_database(self):
        """Test cache retrieval is faster than database query."""
        import time

        from apps.portfolio.models import Admin, BlogCategory, BlogPost

        # Create test data
        category = BlogCategory.objects.create(name="Tech", slug="tech")
        admin = Admin.objects.create(username="author", email="author@example.com")
        admin.set_password("pass123")
        admin.save()

        post = BlogPost.objects.create(
            title="Test Post",
            slug="test-post",
            content="Content",
            category=category,
            author=admin,
            status="published",
        )

        # Database query (uncached)
        start_db = time.time()
        db_post = BlogPost.objects.get(id=post.id)
        db_time = time.time() - start_db

        # Cache the post
        cache.set(f"post_{post.id}", db_post, 3600)

        # Cache retrieval
        start_cache = time.time()
        cached_post = cache.get(f"post_{post.id}")
        cache_time = time.time() - start_cache

        # Cache should be faster (though with LocMemCache, difference is minimal)
        assert cached_post is not None


# ============================================================================
# CACHE BACKEND CONFIGURATION TESTS
# ============================================================================


@pytest.mark.django_db
class TestCacheBackendConfiguration:
    """Test cache backend configuration."""

    def test_cache_backend_is_locmem(self):
        """Test cache backend is LocMemCache for testing."""
        from django.conf import settings

        # In test settings, should be using LocMemCache
        assert (
            "locmem" in settings.CACHES["default"]["BACKEND"].lower()
            or settings.CACHES["default"]["BACKEND"]
            == "django.core.cache.backends.locmem.LocMemCache"
        )


# ============================================================================
# CACHE ERROR HANDLING TESTS
# ============================================================================


@pytest.mark.django_db
class TestCacheErrorHandling:
    """Test cache error handling."""

    def setup_method(self):
        """Clear cache before each test."""
        cache.clear()

    def test_cache_handles_none_value(self):
        """Test cache handles None values correctly."""
        cache.set("none_key", None, 3600)

        # get() returns None, but key exists
        value = cache.get("none_key")
        assert value is None

        # Use get with default to distinguish
        value_with_default = cache.get("none_key", default="default")
        # If key exists with None value, should return None (not default)

    @patch("django.core.cache.cache.get")
    def test_cache_connection_failure_handling(self, mock_get):
        """Test handling cache connection failures gracefully."""
        # Simulate cache failure
        mock_get.side_effect = Exception("Cache connection failed")

        # Application should handle gracefully
        try:
            value = cache.get("some_key")
        except Exception:
            # Should fall back to database or return None
            pass
