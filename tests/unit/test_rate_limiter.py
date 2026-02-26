"""Unit tests for per-user rate limiter."""

import time
from unittest.mock import patch

import pytest

from core.ai_support_bot.security.rate_limiter import RateLimiter


class TestRateLimiter:
    """Test suite for RateLimiter class."""

    def test_allows_first_call(self):
        rl = RateLimiter(max_calls=5, window_seconds=60)
        assert rl.is_allowed(user_id=1) is True

    def test_allows_up_to_max_calls(self):
        rl = RateLimiter(max_calls=3, window_seconds=60)
        assert rl.is_allowed(1) is True
        assert rl.is_allowed(1) is True
        assert rl.is_allowed(1) is True
        # 4th call should be blocked
        assert rl.is_allowed(1) is False

    def test_different_users_independent(self):
        rl = RateLimiter(max_calls=2, window_seconds=60)
        assert rl.is_allowed(1) is True
        assert rl.is_allowed(1) is True
        assert rl.is_allowed(1) is False  # User 1 blocked

        # User 2 should still be allowed
        assert rl.is_allowed(2) is True
        assert rl.is_allowed(2) is True
        assert rl.is_allowed(2) is False  # User 2 also blocked now

    def test_window_expiry_resets(self):
        rl = RateLimiter(max_calls=2, window_seconds=1)
        assert rl.is_allowed(1) is True
        assert rl.is_allowed(1) is True
        assert rl.is_allowed(1) is False

        # Wait for window to expire
        time.sleep(1.1)
        assert rl.is_allowed(1) is True

    def test_remaining_count(self):
        rl = RateLimiter(max_calls=5, window_seconds=60)
        assert rl.remaining(1) == 5
        rl.is_allowed(1)
        assert rl.remaining(1) == 4
        rl.is_allowed(1)
        rl.is_allowed(1)
        assert rl.remaining(1) == 2

    def test_remaining_for_unknown_user(self):
        rl = RateLimiter(max_calls=5, window_seconds=60)
        assert rl.remaining(999) == 5

    def test_reset_single_user(self):
        rl = RateLimiter(max_calls=2, window_seconds=60)
        rl.is_allowed(1)
        rl.is_allowed(1)
        assert rl.is_allowed(1) is False

        rl.reset(1)
        assert rl.is_allowed(1) is True

    def test_reset_does_not_affect_other_users(self):
        rl = RateLimiter(max_calls=2, window_seconds=60)
        rl.is_allowed(1)
        rl.is_allowed(1)
        rl.is_allowed(2)
        rl.is_allowed(2)

        rl.reset(1)
        assert rl.is_allowed(1) is True  # User 1 reset
        assert rl.is_allowed(2) is False  # User 2 still blocked

    def test_reset_all(self):
        rl = RateLimiter(max_calls=1, window_seconds=60)
        rl.is_allowed(1)
        rl.is_allowed(2)
        assert rl.is_allowed(1) is False
        assert rl.is_allowed(2) is False

        rl.reset_all()
        assert rl.is_allowed(1) is True
        assert rl.is_allowed(2) is True

    def test_zero_max_calls_blocks_all(self):
        rl = RateLimiter(max_calls=0, window_seconds=60)
        assert rl.is_allowed(1) is False

    def test_large_user_id(self):
        rl = RateLimiter(max_calls=3, window_seconds=60)
        big_id = 999999999999999999
        assert rl.is_allowed(big_id) is True
