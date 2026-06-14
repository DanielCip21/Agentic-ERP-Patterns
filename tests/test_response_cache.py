"""Tests for ResponseCache — TTL, LRU eviction, stats, and helpers."""

import time

import pytest

from agentic_erp.cache.response_cache import CacheEntry, ResponseCache


# ---------------------------------------------------------------------------
# TestResponseCacheBasic
# ---------------------------------------------------------------------------

class TestResponseCacheBasic:
    def test_get_returns_none_for_missing_key(self):
        cache = ResponseCache()
        assert cache.get("nonexistent") is None

    def test_set_and_get_round_trip(self):
        cache = ResponseCache()
        cache.set("key1", {"data": 42})
        assert cache.get("key1") == {"data": 42}

    def test_get_returns_none_after_ttl_expires(self):
        cache = ResponseCache()
        cache.set("short_lived", "value", ttl=0.01)
        time.sleep(0.02)
        assert cache.get("short_lived") is None

    def test_expired_entry_removed_on_get(self):
        cache = ResponseCache()
        cache.set("expiring", "val", ttl=0.01)
        time.sleep(0.02)
        # The entry is in the store before the get
        initial_size = cache.size
        cache.get("expiring")
        # After get, expired entry should be removed
        assert cache.size < initial_size or cache.size == 0

    def test_lru_eviction_on_max_size(self):
        cache = ResponseCache(max_size=2)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)  # should evict "a" (oldest)
        assert cache.get("a") is None
        assert cache.get("b") == 2
        assert cache.get("c") == 3

    def test_most_recently_used_not_evicted(self):
        cache = ResponseCache(max_size=2)
        cache.set("a", 1)
        cache.set("b", 2)
        # Access "a" to make it recently used
        cache.get("a")
        # Adding "c" should evict "b" (now least recently used)
        cache.set("c", 3)
        assert cache.get("b") is None
        assert cache.get("a") == 1
        assert cache.get("c") == 3

    def test_invalidate_removes_key(self):
        cache = ResponseCache()
        cache.set("to_remove", "value")
        result = cache.invalidate("to_remove")
        assert result is True
        assert cache.get("to_remove") is None

    def test_invalidate_missing_key_returns_false(self):
        cache = ResponseCache()
        result = cache.invalidate("does_not_exist")
        assert result is False


# ---------------------------------------------------------------------------
# TestResponseCacheStats
# ---------------------------------------------------------------------------

class TestResponseCacheStats:
    def test_hit_increments_hits(self):
        cache = ResponseCache()
        cache.set("key", "value")
        cache.get("key")
        assert cache.stats["hits"] == 1

    def test_miss_increments_misses(self):
        cache = ResponseCache()
        cache.get("missing_key")
        assert cache.stats["misses"] == 1

    def test_hit_rate_zero_with_no_calls(self):
        cache = ResponseCache()
        assert cache.hit_rate == 0.0

    def test_hit_rate_calculated_correctly(self):
        cache = ResponseCache()
        cache.set("a", 1)
        cache.set("b", 2)
        cache.get("a")   # hit
        cache.get("b")   # hit
        cache.get("c")   # miss
        assert abs(cache.hit_rate - 2 / 3) < 1e-9


# ---------------------------------------------------------------------------
# TestResponseCacheHelpers
# ---------------------------------------------------------------------------

class TestResponseCacheHelpers:
    def test_make_key_deterministic(self):
        key1 = ResponseCache.make_key("GET", "/api/items", {"page": 1})
        key2 = ResponseCache.make_key("GET", "/api/items", {"page": 1})
        assert key1 == key2

    def test_make_key_different_args_differ(self):
        key1 = ResponseCache.make_key("a",)
        key2 = ResponseCache.make_key("b",)
        assert key1 != key2

    def test_clear_resets_stats_and_store(self):
        cache = ResponseCache()
        cache.set("x", 1)
        cache.get("x")      # hit
        cache.get("y")      # miss
        cache.clear()
        assert cache.size == 0
        assert cache.stats["hits"] == 0
        assert cache.stats["misses"] == 0


# ---------------------------------------------------------------------------
# TestResponseCacheCustomTTL
# ---------------------------------------------------------------------------

class TestResponseCacheCustomTTL:
    def test_custom_ttl_per_entry(self):
        cache = ResponseCache(default_ttl=300.0)
        cache.set("short", "expires_soon", ttl=0.01)
        cache.set("long", "stays_alive", ttl=10.0)
        time.sleep(0.02)
        assert cache.get("short") is None
        assert cache.get("long") == "stays_alive"

    def test_invalidate_prefix(self):
        cache = ResponseCache()
        cache.set("GET:/a/1", "val1")
        cache.set("GET:/a/2", "val2")
        cache.set("GET:/b/1", "val3")
        removed = cache.invalidate_prefix("GET:/a/")
        assert removed == 2
        assert cache.get("GET:/a/1") is None
        assert cache.get("GET:/a/2") is None
        assert cache.get("GET:/b/1") == "val3"
