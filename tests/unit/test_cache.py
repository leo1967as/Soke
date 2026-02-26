"""Unit tests for in-memory cache with TTL."""

import time

import pytest

from core.ai_support_bot.cache.memory_cache import MemoryCache


class TestMemoryCache:
    """Test suite for MemoryCache class."""

    def test_set_and_get(self):
        cache = MemoryCache(default_ttl=60)
        cache.set("question1", "answer1")
        assert cache.get("question1") == "answer1"

    def test_miss_returns_none(self):
        cache = MemoryCache(default_ttl=60)
        assert cache.get("nonexistent") is None

    def test_ttl_expiration(self):
        cache = MemoryCache(default_ttl=1)
        cache.set("key", "value")
        assert cache.get("key") == "value"

        time.sleep(1.1)
        assert cache.get("key") is None

    def test_custom_ttl_override(self):
        cache = MemoryCache(default_ttl=60)
        cache.set("key", "value", ttl=1)

        assert cache.get("key") == "value"
        time.sleep(1.1)
        assert cache.get("key") is None

    def test_overwrite_existing_key(self):
        cache = MemoryCache(default_ttl=60)
        cache.set("key", "v1")
        cache.set("key", "v2")
        assert cache.get("key") == "v2"

    def test_invalidate_existing(self):
        cache = MemoryCache(default_ttl=60)
        cache.set("key", "value")
        assert cache.invalidate("key") is True
        assert cache.get("key") is None

    def test_invalidate_nonexistent(self):
        cache = MemoryCache(default_ttl=60)
        assert cache.invalidate("nope") is False

    def test_clear(self):
        cache = MemoryCache(default_ttl=60)
        cache.set("a", "1")
        cache.set("b", "2")
        cache.set("c", "3")
        count = cache.clear()
        assert count == 3
        assert cache.get("a") is None
        assert cache.size() == 0

    def test_size(self):
        cache = MemoryCache(default_ttl=60)
        assert cache.size() == 0
        cache.set("a", "1")
        assert cache.size() == 1
        cache.set("b", "2")
        assert cache.size() == 2

    def test_cleanup_expired(self):
        cache = MemoryCache(default_ttl=1)
        cache.set("a", "1")
        cache.set("b", "2")

        time.sleep(1.1)

        # Add a fresh entry
        cache.set("c", "3", ttl=60)

        removed = cache.cleanup_expired()
        assert removed == 2
        assert cache.get("c") == "3"
        assert cache.size() == 1

    def test_different_keys_same_hash_collision_unlikely(self):
        cache = MemoryCache(default_ttl=60)
        cache.set("key_alpha", "val_alpha")
        cache.set("key_beta", "val_beta")
        assert cache.get("key_alpha") == "val_alpha"
        assert cache.get("key_beta") == "val_beta"

    def test_unicode_keys(self):
        cache = MemoryCache(default_ttl=60)
        cache.set("สินค้าราคาเท่าไหร่", "100 บาท")
        assert cache.get("สินค้าราคาเท่าไหร่") == "100 บาท"

    def test_empty_string_key(self):
        cache = MemoryCache(default_ttl=60)
        cache.set("", "empty_key_value")
        assert cache.get("") == "empty_key_value"

    def test_large_value(self):
        cache = MemoryCache(default_ttl=60)
        big_val = "x" * 100_000
        cache.set("big", big_val)
        assert cache.get("big") == big_val
