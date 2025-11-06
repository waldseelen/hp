"""
Mock implementation of Redis client for testing

Provides an in-memory key-value store that simulates
Redis behavior without requiring a running server.
"""

import time
from typing import Any, Dict, List, Optional, Union


class MockRedisClient:
    """
    Mock Redis client for testing

    Simulates basic Redis operations in memory.
    Supports common operations like get, set, delete, expire, etc.

    Usage in tests:
        from tests.mocks import MockRedisClient

        @pytest.fixture
        def mock_redis(monkeypatch):
            mock_client = MockRedisClient()
            monkeypatch.setattr("redis.Redis", lambda *args, **kwargs: mock_client)
            return mock_client

        def test_cache(mock_redis):
            mock_redis.set("key", "value")
            assert mock_redis.get("key") == "value"
    """

    def __init__(self, **kwargs):
        self.data: Dict[str, Any] = {}
        self.expiry: Dict[str, float] = {}
        self.lists: Dict[str, List[Any]] = {}
        self.sets: Dict[str, set] = {}
        self.hashes: Dict[str, Dict[str, Any]] = {}

    def _is_expired(self, key: str) -> bool:
        """Check if key has expired"""
        if key in self.expiry:
            if time.time() > self.expiry[key]:
                self._cleanup_key(key)
                return True
        return False

    def _cleanup_key(self, key: str):
        """Remove expired key from all stores"""
        self.data.pop(key, None)
        self.expiry.pop(key, None)
        self.lists.pop(key, None)
        self.sets.pop(key, None)
        self.hashes.pop(key, None)

    # String operations
    def get(self, key: str) -> Optional[bytes]:
        """Get value by key"""
        if self._is_expired(key):
            return None
        value = self.data.get(key)
        if value is not None and isinstance(value, str):
            return value.encode()
        return value

    def set(
        self,
        key: str,
        value: Union[str, bytes],
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """Set key to value with optional expiry"""
        # Check nx (only set if not exists)
        if nx and key in self.data and not self._is_expired(key):
            return False

        # Check xx (only set if exists)
        if xx and (key not in self.data or self._is_expired(key)):
            return False

        # Convert bytes to string for storage
        if isinstance(value, bytes):
            value = value.decode()

        self.data[key] = value

        # Set expiry
        if ex is not None:
            self.expiry[key] = time.time() + ex
        elif px is not None:
            self.expiry[key] = time.time() + (px / 1000)

        return True

    def delete(self, *keys: str) -> int:
        """Delete one or more keys"""
        count = 0
        for key in keys:
            if key in self.data:
                self._cleanup_key(key)
                count += 1
        return count

    def exists(self, *keys: str) -> int:
        """Check if keys exist"""
        count = 0
        for key in keys:
            if key in self.data and not self._is_expired(key):
                count += 1
        return count

    def expire(self, key: str, seconds: int) -> bool:
        """Set expiry time for key"""
        if key not in self.data or self._is_expired(key):
            return False
        self.expiry[key] = time.time() + seconds
        return True

    def ttl(self, key: str) -> int:
        """Get time to live for key"""
        if key not in self.data or self._is_expired(key):
            return -2  # Key doesn't exist
        if key not in self.expiry:
            return -1  # Key exists but has no expiry
        remaining = int(self.expiry[key] - time.time())
        return max(remaining, -2)

    def keys(self, pattern: str = "*") -> List[bytes]:
        """Get all keys matching pattern"""
        # Simple pattern matching (just * wildcard)
        if pattern == "*":
            return [k.encode() for k in self.data.keys() if not self._is_expired(k)]

        # Basic pattern matching
        import re

        regex_pattern = pattern.replace("*", ".*")
        regex = re.compile(regex_pattern)
        return [
            k.encode()
            for k in self.data.keys()
            if not self._is_expired(k) and regex.match(k)
        ]

    def flushdb(self) -> bool:
        """Clear all keys in current database"""
        self.data.clear()
        self.expiry.clear()
        self.lists.clear()
        self.sets.clear()
        self.hashes.clear()
        return True

    def flushall(self) -> bool:
        """Clear all keys in all databases"""
        return self.flushdb()

    # List operations
    def lpush(self, key: str, *values: Any) -> int:
        """Push values to head of list"""
        if key not in self.lists:
            self.lists[key] = []
        for value in reversed(values):
            self.lists[key].insert(0, value)
        return len(self.lists[key])

    def rpush(self, key: str, *values: Any) -> int:
        """Push values to tail of list"""
        if key not in self.lists:
            self.lists[key] = []
        self.lists[key].extend(values)
        return len(self.lists[key])

    def lpop(self, key: str) -> Optional[Any]:
        """Pop value from head of list"""
        if key not in self.lists or not self.lists[key]:
            return None
        return self.lists[key].pop(0)

    def rpop(self, key: str) -> Optional[Any]:
        """Pop value from tail of list"""
        if key not in self.lists or not self.lists[key]:
            return None
        return self.lists[key].pop()

    def lrange(self, key: str, start: int, stop: int) -> List[Any]:
        """Get range of elements from list"""
        if key not in self.lists:
            return []
        return self.lists[key][start : stop + 1]

    def llen(self, key: str) -> int:
        """Get length of list"""
        return len(self.lists.get(key, []))

    # Set operations
    def sadd(self, key: str, *values: Any) -> int:
        """Add values to set"""
        if key not in self.sets:
            self.sets[key] = set()
        before = len(self.sets[key])
        self.sets[key].update(values)
        return len(self.sets[key]) - before

    def srem(self, key: str, *values: Any) -> int:
        """Remove values from set"""
        if key not in self.sets:
            return 0
        before = len(self.sets[key])
        self.sets[key].difference_update(values)
        return before - len(self.sets[key])

    def smembers(self, key: str) -> set:
        """Get all members of set"""
        return self.sets.get(key, set()).copy()

    def sismember(self, key: str, value: Any) -> bool:
        """Check if value is member of set"""
        return value in self.sets.get(key, set())

    # Hash operations
    def hset(self, key: str, field: str, value: Any) -> int:
        """Set hash field to value"""
        if key not in self.hashes:
            self.hashes[key] = {}
        is_new = field not in self.hashes[key]
        self.hashes[key][field] = value
        return 1 if is_new else 0

    def hget(self, key: str, field: str) -> Optional[Any]:
        """Get hash field value"""
        return self.hashes.get(key, {}).get(field)

    def hgetall(self, key: str) -> Dict[str, Any]:
        """Get all hash fields and values"""
        return self.hashes.get(key, {}).copy()

    def hdel(self, key: str, *fields: str) -> int:
        """Delete hash fields"""
        if key not in self.hashes:
            return 0
        count = 0
        for field in fields:
            if field in self.hashes[key]:
                del self.hashes[key][field]
                count += 1
        return count

    def hexists(self, key: str, field: str) -> bool:
        """Check if hash field exists"""
        return field in self.hashes.get(key, {})

    # Connection management
    def ping(self) -> bool:
        """Ping the server"""
        return True

    def close(self):
        """Close connection (no-op for mock)"""
        pass

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
