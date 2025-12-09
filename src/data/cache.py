"""Filing cache management for SEC EDGAR data."""

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from src.config import settings


class FilingCache:
    """
    Simple file-based cache for SEC filings.

    Uses JSON files with TTL-based expiration.
    """

    def __init__(
        self,
        cache_dir: Path | None = None,
        ttl_seconds: int | None = None,
    ):
        self.cache_dir = cache_dir or settings.cache_dir
        self.ttl_seconds = ttl_seconds or settings.cache_ttl_seconds
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, key: str) -> str:
        """Generate a filesystem-safe cache key."""
        return hashlib.sha256(key.encode()).hexdigest()[:32]

    def _get_cache_path(self, key: str) -> Path:
        """Get the file path for a cache key."""
        cache_key = self._get_cache_key(key)
        return self.cache_dir / f"{cache_key}.json"

    def get(self, key: str) -> Any | None:
        """
        Get a value from cache if it exists and hasn't expired.

        Returns None if not found or expired.
        """
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path) as f:
                cached = json.load(f)

            # Check expiration
            if time.time() > cached.get("expires_at", 0):
                cache_path.unlink(missing_ok=True)
                return None

            return cached.get("value")
        except (json.JSONDecodeError, OSError):
            # Corrupted cache file, remove it
            cache_path.unlink(missing_ok=True)
            return None

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        """Store a value in cache with optional custom TTL."""
        ttl = ttl_seconds or self.ttl_seconds
        cache_path = self._get_cache_path(key)

        cached = {
            "key": key,
            "value": value,
            "created_at": time.time(),
            "expires_at": time.time() + ttl,
        }

        with open(cache_path, "w") as f:
            json.dump(cached, f)

    def delete(self, key: str) -> bool:
        """Delete a cache entry. Returns True if deleted."""
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            cache_path.unlink()
            return True
        return False

    def clear(self) -> int:
        """Clear all cache entries. Returns number of entries cleared."""
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            count += 1
        return count

    def clear_expired(self) -> int:
        """Clear only expired entries. Returns number of entries cleared."""
        count = 0
        now = time.time()

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file) as f:
                    cached = json.load(f)
                if now > cached.get("expires_at", 0):
                    cache_file.unlink()
                    count += 1
            except (json.JSONDecodeError, OSError):
                cache_file.unlink()
                count += 1

        return count


# Global cache instance
_cache: FilingCache | None = None


def get_cache() -> FilingCache:
    """Get or create the global cache instance."""
    global _cache
    if _cache is None:
        _cache = FilingCache()
    return _cache
