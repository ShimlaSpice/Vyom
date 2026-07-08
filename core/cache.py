"""Thread-safe in-memory cache for application services."""

from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass
from threading import RLock
from typing import Generic, TypeVar

from config import Settings

T = TypeVar("T")


@dataclass(slots=True)
class CacheEntry(Generic[T]):
    """Store a cached value with an absolute expiry timestamp."""

    value: T
    expires_at: float | None

    def is_expired(self) -> bool:
        """Return whether the entry is expired."""

        return self.expires_at is not None and time.monotonic() >= self.expires_at


class CacheManager(Generic[T]):
    """Simple bounded TTL cache suitable for local application state."""

    def __init__(self, settings: Settings) -> None:
        self._default_ttl_seconds = settings.cache.default_ttl_seconds
        self._max_items = settings.cache.max_items
        self._lock = RLock()
        self._store: OrderedDict[str, CacheEntry[T]] = OrderedDict()

    def set(self, key: str, value: T, ttl_seconds: int | None = None) -> None:
        """Insert or update a cache entry."""

        ttl = self._default_ttl_seconds if ttl_seconds is None else ttl_seconds
        expires_at = None if ttl <= 0 else time.monotonic() + ttl
        with self._lock:
            self._store[key] = CacheEntry(value=value, expires_at=expires_at)
            self._store.move_to_end(key)
            self._enforce_capacity()

    def get(self, key: str, default: T | None = None) -> T | None:
        """Return a cached value if it exists and is not expired."""

        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return default
            if entry.is_expired():
                self._store.pop(key, None)
                return default
            self._store.move_to_end(key)
            return entry.value

    def delete(self, key: str) -> None:
        """Remove a cache entry when present."""

        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        """Remove all cache entries."""

        with self._lock:
            self._store.clear()

    def cleanup(self) -> None:
        """Purge expired entries from the cache."""

        with self._lock:
            expired_keys = [key for key, entry in self._store.items() if entry.is_expired()]
            for key in expired_keys:
                self._store.pop(key, None)

    def _enforce_capacity(self) -> None:
        """Trim the cache when it exceeds its configured capacity."""

        self.cleanup()
        while len(self._store) > self._max_items:
            self._store.popitem(last=False)
