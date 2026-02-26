"""Per-user rate limiter to prevent abuse and quota exhaustion."""

import time
from collections import defaultdict


class RateLimiter:
    """Sliding-window rate limiter keyed by user ID.

    Args:
        max_calls: Maximum allowed calls within the window.
        window_seconds: Duration of the sliding window in seconds.
    """

    def __init__(self, max_calls: int = 20, window_seconds: int = 3600):
        self.max_calls = max_calls
        self.window = window_seconds
        self._records: dict[int, list[float]] = defaultdict(list)

    def is_allowed(self, user_id: int) -> bool:
        """Check if user_id is within the rate limit.

        Returns True if the call is allowed, False if rate-limited.
        """
        now = time.monotonic()
        calls = self._records[user_id]

        # Evict expired entries
        self._records[user_id] = [t for t in calls if now - t < self.window]

        if len(self._records[user_id]) >= self.max_calls:
            return False

        self._records[user_id].append(now)
        return True

    def remaining(self, user_id: int) -> int:
        """Return how many calls the user has left in the current window."""
        now = time.monotonic()
        calls = self._records.get(user_id, [])
        active = [t for t in calls if now - t < self.window]
        return max(0, self.max_calls - len(active))

    def time_until_reset(self, user_id: int) -> float:
        """Return the number of seconds until the user can make another call."""
        now = time.monotonic()
        calls = self._records.get(user_id, [])
        active = [t for t in calls if now - t < self.window]
        
        if len(active) < self.max_calls:
            return 0.0
            
        # The oldest active call dictates when the next slot opens up
        oldest_call = active[0]
        return max(0.0, self.window - (now - oldest_call))

    def reset(self, user_id: int) -> None:
        """Reset rate limit for a specific user (admin use)."""
        self._records.pop(user_id, None)

    def reset_all(self) -> None:
        """Reset all rate limits."""
        self._records.clear()
