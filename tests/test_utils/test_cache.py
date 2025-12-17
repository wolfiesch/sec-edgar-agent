"""Tests for filing cache."""

import json
import tempfile
import time
from collections.abc import Generator
from pathlib import Path

import pytest

from src.data.cache import FilingCache


class TestFilingCache:
    """Tests for FilingCache class."""

    @pytest.fixture
    def temp_cache_dir(self) -> Generator[Path, None, None]:
        """Create a temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def cache(self, temp_cache_dir: Path) -> FilingCache:
        """Create a cache instance with temporary directory."""
        return FilingCache(cache_dir=temp_cache_dir, ttl_seconds=60)

    def test_init_creates_directory(self, temp_cache_dir: Path) -> None:
        """Test that initialization creates cache directory."""
        cache_dir = temp_cache_dir / "new_cache"
        assert not cache_dir.exists()

        FilingCache(cache_dir=cache_dir)
        assert cache_dir.exists()
        assert cache_dir.is_dir()

    def test_get_cache_key_is_consistent(self, cache: FilingCache) -> None:
        """Test that same key produces same cache key."""
        key1 = cache._get_cache_key("test_key")
        key2 = cache._get_cache_key("test_key")
        assert key1 == key2

    def test_get_cache_key_is_unique(self, cache: FilingCache) -> None:
        """Test that different keys produce different cache keys."""
        key1 = cache._get_cache_key("key1")
        key2 = cache._get_cache_key("key2")
        assert key1 != key2

    def test_get_cache_key_is_filesystem_safe(self, cache: FilingCache) -> None:
        """Test that cache keys are filesystem safe."""
        key = cache._get_cache_key("key/with/slashes")
        assert "/" not in key
        assert "\\" not in key
        assert len(key) == 32  # SHA256 truncated to 32 chars

    def test_set_and_get(self, cache: FilingCache) -> None:
        """Test setting and getting a value."""
        cache.set("test_key", {"data": "value"})
        result = cache.get("test_key")
        assert result == {"data": "value"}

    def test_get_nonexistent_key(self, cache: FilingCache) -> None:
        """Test getting a nonexistent key returns None."""
        result = cache.get("nonexistent")
        assert result is None

    def test_get_expired_key(self, cache: FilingCache) -> None:
        """Test that expired keys return None."""
        # Set with very short TTL and wait for expiration
        cache.set("test_key", "value", ttl_seconds=0.005)  # 5ms TTL
        time.sleep(0.02)  # Wait 20ms for expiration

        result = cache.get("test_key")
        assert result is None

    def test_get_expired_key_deletes_file(
        self, cache: FilingCache, temp_cache_dir: Path
    ) -> None:
        """Test that getting expired key deletes the file."""
        cache.set("test_key", "value", ttl_seconds=0.005)  # 5ms TTL
        time.sleep(0.02)  # Wait 20ms for expiration

        cache.get("test_key")

        # File should be deleted
        cache_files = list(temp_cache_dir.glob("*.json"))
        assert len(cache_files) == 0

    def test_set_with_custom_ttl(self, cache: FilingCache) -> None:
        """Test setting with custom TTL."""
        cache.set("test_key", "value", ttl_seconds=3600)
        result = cache.get("test_key")
        assert result == "value"

    def test_delete_existing_key(self, cache: FilingCache) -> None:
        """Test deleting an existing key."""
        cache.set("test_key", "value")
        result = cache.delete("test_key")
        assert result is True
        assert cache.get("test_key") is None

    def test_delete_nonexistent_key(self, cache: FilingCache) -> None:
        """Test deleting a nonexistent key."""
        result = cache.delete("nonexistent")
        assert result is False

    def test_clear_removes_all_entries(self, cache: FilingCache) -> None:
        """Test that clear removes all entries."""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        count = cache.clear()
        assert count == 3
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") is None

    def test_clear_empty_cache(self, cache: FilingCache) -> None:
        """Test clearing an empty cache."""
        count = cache.clear()
        assert count == 0

    def test_clear_expired_only_removes_expired(self, cache: FilingCache) -> None:
        """Test that clear_expired only removes expired entries."""
        # Set one expired, one valid
        cache.set("key1", "value1", ttl_seconds=1)
        # Should exist immediately
        assert cache.get("key1") == "value1"
        time.sleep(1.1) # Wait for expiration
        cache.set("key2", "value2", ttl_seconds=60)

        count = cache.clear_expired()
        assert count == 1
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"

    def test_clear_expired_no_expired_entries(self, cache: FilingCache) -> None:
        """Test clear_expired when no entries are expired."""
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        count = cache.clear_expired()
        assert count == 0
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"

    def test_handles_corrupted_cache_file(
        self, cache: FilingCache, temp_cache_dir: Path
    ) -> None:
        """Test that corrupted cache files are handled gracefully."""
        # Create a corrupted cache file
        cache_key = cache._get_cache_key("test_key")
        cache_path = temp_cache_dir / f"{cache_key}.json"
        cache_path.write_text("not valid json{{{")

        # Should return None and delete the file
        result = cache.get("test_key")
        assert result is None
        assert not cache_path.exists()

    def test_stores_metadata(self, cache: FilingCache, temp_cache_dir: Path) -> None:
        """Test that cache stores metadata correctly."""
        cache.set("test_key", {"data": "value"})

        # Read the cache file directly
        cache_key = cache._get_cache_key("test_key")
        cache_path = temp_cache_dir / f"{cache_key}.json"

        with open(cache_path) as f:
            cached = json.load(f)

        assert "key" in cached
        assert "value" in cached
        assert "created_at" in cached
        assert "expires_at" in cached
        assert cached["key"] == "test_key"
        assert cached["value"] == {"data": "value"}


class TestFilingCacheDataTypes:
    """Tests for caching different data types."""

    @pytest.fixture
    def cache(self) -> Generator[FilingCache, None, None]:
        """Create a cache instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield FilingCache(cache_dir=Path(tmpdir), ttl_seconds=60)

    def test_cache_dict(self, cache: FilingCache) -> None:
        """Test caching a dictionary."""
        data = {"ticker": "AAPL", "name": "Apple Inc."}
        cache.set("company", data)
        assert cache.get("company") == data

    def test_cache_list(self, cache: FilingCache) -> None:
        """Test caching a list."""
        data = ["10-K", "10-Q", "8-K"]
        cache.set("forms", data)
        assert cache.get("forms") == data

    def test_cache_string(self, cache: FilingCache) -> None:
        """Test caching a string."""
        data = "This is a test string"
        cache.set("text", data)
        assert cache.get("text") == data

    def test_cache_number(self, cache: FilingCache) -> None:
        """Test caching numbers."""
        cache.set("int", 42)
        cache.set("float", 3.14)
        assert cache.get("int") == 42
        assert cache.get("float") == 3.14

    def test_cache_nested_structure(self, cache: FilingCache) -> None:
        """Test caching nested data structures."""
        data = {
            "company": {"ticker": "AAPL", "name": "Apple Inc."},
            "filings": [
                {"form": "10-K", "date": "2024-10-31"},
                {"form": "10-Q", "date": "2024-07-27"},
            ],
        }
        cache.set("complex", data)
        assert cache.get("complex") == data


class TestGetCache:
    """Tests for the global cache getter."""

    def test_get_cache_creates_instance(self) -> None:
        """Test that get_cache creates an instance."""
        from src.data.cache import get_cache

        cache = get_cache()
        assert isinstance(cache, FilingCache)

    def test_get_cache_returns_same_instance(self) -> None:
        """Test that get_cache returns the same instance."""
        from src.data.cache import get_cache

        cache1 = get_cache()
        cache2 = get_cache()
        assert cache1 is cache2
