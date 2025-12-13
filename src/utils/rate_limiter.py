"""Rate limiter for SEC EDGAR API compliance."""

import asyncio
import time
from collections import deque
from threading import Lock


class RateLimiter:
    """
    Token bucket rate limiter for SEC EDGAR API.

    SEC requires max 10 requests per second.
    """

    def __init__(self, requests_per_second: float = 10.0):
        """Configure limits and internal tracking structures."""
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self._lock = Lock()
        self._last_request_time = 0.0
        # Track request times for burst detection
        self._request_times: deque[float] = deque(maxlen=int(requests_per_second))

    def wait(self) -> None:
        """Block until a request can be made within rate limit."""
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request_time

            if elapsed < self.min_interval:
                sleep_time = self.min_interval - elapsed
                time.sleep(sleep_time)

            self._last_request_time = time.monotonic()
            self._request_times.append(self._last_request_time)

    async def wait_async(self) -> None:
        """Async version of wait."""
        # Calculate wait time synchronously
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request_time

            if elapsed < self.min_interval:
                sleep_time = self.min_interval - elapsed
            else:
                sleep_time = 0

            self._last_request_time = time.monotonic() + sleep_time
            self._request_times.append(self._last_request_time)

        # Sleep outside the lock
        if sleep_time > 0:
            await asyncio.sleep(sleep_time)

    def get_requests_in_last_second(self) -> int:
        """Return number of requests made in the last second."""
        now = time.monotonic()
        cutoff = now - 1.0
        return sum(1 for t in self._request_times if t > cutoff)


# Global rate limiter instance
_rate_limiter: RateLimiter | None = None


def get_rate_limiter(requests_per_second: float = 10.0) -> RateLimiter:
    """Get or create the global rate limiter."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(requests_per_second)
    return _rate_limiter
