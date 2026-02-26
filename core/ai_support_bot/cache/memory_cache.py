"""Thread-safe in-memory cache with TTL expiration.

This is the Phase 0 cache — will be replaced by Redis in Phase 1.
"""

import hashlib
import threading
import time
from dataclasses import dataclass


@dataclass
class _CacheEntry:
    value: str
    expires_at: float


class MemoryCache:
    """Simple in-memory key-value cache with time-to-live.

    Thread-safe via threading.Lock.
    """

    def __init__(self, default_ttl: int = 3600):
        self._store: dict[str, _CacheEntry] = {}
        self._lock = threading.Lock()
        self.default_ttl = default_ttl

    @staticmethod
    def _hash_key(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]

    def get(self, key: str) -> str | None:
        """Retrieve a cached value. Returns None if missing or expired."""
        hashed = self._hash_key(key)
        with self._lock:
            entry = self._store.get(hashed)
            if entry is None:
                return None
            if time.monotonic() > entry.expires_at:
                del self._store[hashed]
                return None
            return entry.value

    def set(self, key: str, value: str, ttl: int | None = None) -> None:
        """Store a value with optional TTL override."""
        hashed = self._hash_key(key)
        ttl = ttl if ttl is not None else self.default_ttl
        with self._lock:
            self._store[hashed] = _CacheEntry(
                value=value,
                expires_at=time.monotonic() + ttl,
            )

    def invalidate(self, key: str) -> bool:
        """Remove a specific key. Returns True if it existed."""
        hashed = self._hash_key(key)
        with self._lock:
            return self._store.pop(hashed, None) is not None

    def clear(self) -> int:
        """Clear all entries. Returns count of removed items."""
        with self._lock:
            count = len(self._store)
            self._store.clear()
            return count

    def size(self) -> int:
        """Return current number of (possibly expired) entries."""
        return len(self._store)

    def cleanup_expired(self) -> int:
        """Remove all expired entries. Returns count of removed items."""
        now = time.monotonic()
        removed = 0
        with self._lock:
            expired_keys = [k for k, v in self._store.items() if now > v.expires_at]
            for k in expired_keys:
                del self._store[k]
                removed += 1
        return removed
