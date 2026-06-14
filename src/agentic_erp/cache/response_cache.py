"""TTL-based LRU response cache for agents and connectors."""

from __future__ import annotations

import hashlib
import json
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any


@dataclass
class CacheEntry:
    value: Any
    expires_at: float


class ResponseCache:
    """Thread-safe TTL + LRU in-memory cache.

    Entries expire after ``default_ttl`` seconds. When ``max_size`` is reached
    the least-recently-used entry is evicted first.

    Usage::

        from agentic_erp.cache.response_cache import ResponseCache

        cache = ResponseCache(default_ttl=300.0, max_size=512)
        cache.set("key", {"data": [1, 2, 3]})
        value = cache.get("key")   # → {"data": [1, 2, 3]}

        # With a custom TTL per entry
        cache.set("short", "expires soon", ttl=10.0)

        print(cache.stats)
        # {"hits": 1, "misses": 0, "size": 2, "hit_rate": 1.0}
    """

    def __init__(self, default_ttl: float = 300.0, max_size: int = 512) -> None:
        self._store: OrderedDict[str, CacheEntry] = OrderedDict()
        self._default_ttl = default_ttl
        self._max_size = max_size
        self._hits = 0
        self._misses = 0

    # --- Core operations ---

    def get(self, key: str) -> Any | None:
        """Return cached value or ``None`` if missing / expired."""
        entry = self._store.get(key)
        if entry is None:
            self._misses += 1
            return None
        if time.monotonic() > entry.expires_at:
            del self._store[key]
            self._misses += 1
            return None
        self._store.move_to_end(key)
        self._hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        """Store *value* under *key* with an optional per-entry TTL."""
        expires_at = time.monotonic() + (ttl if ttl is not None else self._default_ttl)
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = CacheEntry(value=value, expires_at=expires_at)
        while len(self._store) > self._max_size:
            self._store.popitem(last=False)  # evict LRU

    def invalidate(self, key: str) -> bool:
        """Remove *key* — returns True if it was present."""
        return self._store.pop(key, None) is not None

    def invalidate_prefix(self, prefix: str) -> int:
        """Remove all keys that start with *prefix* — returns count evicted."""
        keys = [k for k in self._store if k.startswith(prefix)]
        for k in keys:
            del self._store[k]
        return len(keys)

    def clear(self) -> None:
        """Flush all entries and reset hit/miss counters."""
        self._store.clear()
        self._hits = 0
        self._misses = 0

    # --- Helpers ---

    @staticmethod
    def make_key(*parts: Any) -> str:
        """Deterministic cache key from arbitrary parts (JSON-serialised + SHA-256)."""
        raw = json.dumps(parts, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    # --- Observability ---

    @property
    def size(self) -> int:
        return len(self._store)

    @property
    def hit_rate(self) -> float:
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "hits": self._hits,
            "misses": self._misses,
            "size": self.size,
            "hit_rate": round(self.hit_rate, 3),
            "max_size": self._max_size,
            "default_ttl": self._default_ttl,
        }
