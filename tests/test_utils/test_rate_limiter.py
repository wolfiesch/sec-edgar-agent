"""Tests for rate limiter."""

import time

import pytest

from src.utils.rate_limiter import RateLimiter, get_rate_limiter


class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_init_default_rate(self) -> None:
        """Test initialization with default rate."""
        limiter = RateLimiter()
        assert limiter.requests_per_second == 10.0
        assert limiter.min_interval == 0.1

    def test_init_custom_rate(self) -> None:
        """Test initialization with custom rate."""
        limiter = RateLimiter(requests_per_second=5.0)
        assert limiter.requests_per_second == 5.0
        assert limiter.min_interval == 0.2

    def test_wait_enforces_minimum_interval(self) -> None:
        """Test that wait enforces minimum interval between requests."""
        limiter = RateLimiter(requests_per_second=10.0)

        start = time.monotonic()
        limiter.wait()
        limiter.wait()
        elapsed = time.monotonic() - start

        # Should take at least 0.1 seconds for two requests
        assert elapsed >= 0.1

    def test_wait_multiple_requests(self) -> None:
        """Test multiple requests respect rate limit."""
        limiter = RateLimiter(requests_per_second=20.0)  # 50ms per request

        start = time.monotonic()
        for _ in range(5):
            limiter.wait()
        elapsed = time.monotonic() - start

        # 5 requests at 50ms each = ~200ms minimum
        assert elapsed >= 0.2

    def test_get_requests_in_last_second(self) -> None:
        """Test tracking requests in the last second."""
        limiter = RateLimiter(requests_per_second=10.0)

        # Make 3 requests
        limiter.wait()
        limiter.wait()
        limiter.wait()

        count = limiter.get_requests_in_last_second()
        assert count == 3

    def test_requests_in_last_second_expires(self) -> None:
        """Test that old requests don't count."""
        limiter = RateLimiter(requests_per_second=100.0)  # Fast for testing

        # Make a request
        limiter.wait()
        assert limiter.get_requests_in_last_second() >= 1

        # Wait for it to expire
        time.sleep(1.1)
        assert limiter.get_requests_in_last_second() == 0

    @pytest.mark.asyncio
    async def test_wait_async(self) -> None:
        """Test async wait method."""
        limiter = RateLimiter(requests_per_second=10.0)

        start = time.monotonic()
        await limiter.wait_async()
        await limiter.wait_async()
        elapsed = time.monotonic() - start

        # Should take at least 0.1 seconds
        assert elapsed >= 0.1

    @pytest.mark.asyncio
    async def test_wait_async_multiple_requests(self) -> None:
        """Test multiple async requests."""
        limiter = RateLimiter(requests_per_second=20.0)

        start = time.monotonic()
        for _ in range(4):
            await limiter.wait_async()
        elapsed = time.monotonic() - start

        # 4 requests at 50ms each = ~150ms minimum
        assert elapsed >= 0.15


class TestRateLimiterThreadSafety:
    """Tests for thread safety (basic checks)."""

    def test_concurrent_wait_calls(self) -> None:
        """Test that concurrent wait calls don't interfere."""
        import threading

        limiter = RateLimiter(requests_per_second=50.0)
        results: list[float] = []

        def make_request() -> None:
            limiter.wait()
            results.append(time.monotonic())

        # Create multiple threads
        threads = [threading.Thread(target=make_request) for _ in range(10)]

        start = time.monotonic()
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        elapsed = time.monotonic() - start

        # All requests should complete
        assert len(results) == 10
        # Should take at least (10 * 0.02s = 0.2s)
        assert elapsed >= 0.18


class TestGetRateLimiter:
    """Tests for the global rate limiter getter."""

    def test_get_rate_limiter_creates_instance(self) -> None:
        """Test that get_rate_limiter creates an instance."""
        limiter = get_rate_limiter()
        assert isinstance(limiter, RateLimiter)
        assert limiter.requests_per_second == 10.0

    def test_get_rate_limiter_returns_same_instance(self) -> None:
        """Test that get_rate_limiter returns the same instance."""
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()
        assert limiter1 is limiter2


class TestRateLimiterEdgeCases:
    """Tests for edge cases."""

    def test_very_low_rate(self) -> None:
        """Test with very low request rate."""
        limiter = RateLimiter(requests_per_second=1.0)
        assert limiter.min_interval == 1.0

        start = time.monotonic()
        limiter.wait()
        limiter.wait()
        elapsed = time.monotonic() - start

        # Should take at least 1 second
        assert elapsed >= 1.0

    def test_very_high_rate(self) -> None:
        """Test with very high request rate."""
        limiter = RateLimiter(requests_per_second=1000.0)
        assert limiter.min_interval == 0.001

        # Should complete quickly
        start = time.monotonic()
        for _ in range(10):
            limiter.wait()
        elapsed = time.monotonic() - start

        # 10 requests at 1ms each = ~10ms
        assert elapsed < 0.1  # Should be very fast

    def test_first_request_no_wait(self) -> None:
        """Test that first request doesn't wait."""
        limiter = RateLimiter(requests_per_second=1.0)

        start = time.monotonic()
        limiter.wait()
        elapsed = time.monotonic() - start

        # First request should be nearly instant
        assert elapsed < 0.01
