import time

from app.core.rate_limiter import InMemoryRateLimiter


def test_rate_limiter_allows_under_threshold():
    """Verify rate limiter allows requests within threshold."""
    limiter = InMemoryRateLimiter()
    ip = "192.168.1.1"

    for _ in range(3):
        assert limiter.is_allowed(ip, max_requests=3, window_seconds=60) is True


def test_rate_limiter_blocks_over_threshold():
    """Verify rate limiter blocks requests exceeding threshold."""
    limiter = InMemoryRateLimiter()
    ip = "192.168.1.2"

    for _ in range(3):
        limiter.is_allowed(ip, max_requests=3, window_seconds=60)

    # 4th request must be blocked
    assert limiter.is_allowed(ip, max_requests=3, window_seconds=60) is False


def test_rate_limiter_resets_after_window():
    """Verify rate limiter allows requests again after window expires."""
    limiter = InMemoryRateLimiter()
    ip = "192.168.1.3"

    for _ in range(2):
        assert limiter.is_allowed(ip, max_requests=2, window_seconds=1) is True

    # 3rd request blocked
    assert limiter.is_allowed(ip, max_requests=2, window_seconds=1) is False

    # Wait for 1-second window to expire
    time.sleep(1.1)

    # Now allowed again
    assert limiter.is_allowed(ip, max_requests=2, window_seconds=1) is True


def test_rate_limiter_keys_isolated():
    """Verify rate limiter tracks different IP addresses independently."""
    limiter = InMemoryRateLimiter()
    ip1 = "10.0.0.1"
    ip2 = "10.0.0.2"

    # Fill ip1
    for _ in range(2):
        limiter.is_allowed(ip1, max_requests=2, window_seconds=60)
    assert limiter.is_allowed(ip1, max_requests=2, window_seconds=60) is False

    # ip2 is still completely fresh
    assert limiter.is_allowed(ip2, max_requests=2, window_seconds=60) is True
