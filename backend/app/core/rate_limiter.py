import time
from collections import defaultdict, deque


class InMemoryRateLimiter:
    """
    Sliding window in-memory rate limiter.
    Tracks request timestamps per key (e.g. client IP) and purges expired entries.
    """

    def __init__(self) -> None:
        self._records: dict[str, deque[float]] = defaultdict(deque)

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """
        Check if request is permitted under rate limit threshold.
        Returns True if allowed, False if blocked.
        """
        now = time.time()
        cutoff = now - window_seconds
        timestamps = self._records[key]

        # Purge timestamps outside the current window
        while timestamps and timestamps[0] <= cutoff:
            timestamps.popleft()

        if len(timestamps) >= max_requests:
            return False

        timestamps.append(now)
        return True

    def reset(self) -> None:
        """Clear all tracking state."""
        self._records.clear()


# Singleton instance for authentication endpoints
auth_rate_limiter = InMemoryRateLimiter()
