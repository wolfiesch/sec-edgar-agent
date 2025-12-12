"""API middleware for authentication and rate limiting."""

import logging
import time
from collections import defaultdict
from typing import Callable

from fastapi import HTTPException, Request, Security
from fastapi.security.api_key import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware

from src.api.config import settings

logger = logging.getLogger(__name__)

# API Key header definition - reusable across routes
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str | None = Security(api_key_header)) -> str:
    """
    Verify API key for protected endpoints.

    Usage:
        @router.post("/protected")
        async def protected_endpoint(api_key: str = Depends(verify_api_key)):
            ...
    """
    if api_key is None:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Include X-API-Key header.",
        )
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key.",
        )
    return api_key


async def optional_api_key(api_key: str | None = Security(api_key_header)) -> str | None:
    """
    Optional API key verification - returns None if not provided, validates if provided.

    Useful for endpoints that are public but offer enhanced features with API key.
    """
    if api_key is not None and api_key != settings.API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key.",
        )
    return api_key


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Token bucket rate limiting middleware.

    Limits requests per client IP address to prevent abuse.
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        # Track request counts per IP: {ip: {"minute": [(timestamp, count)], "hour": [(timestamp, count)]}}
        self.request_counts: dict[str, dict[str, list[tuple[float, int]]]] = defaultdict(
            lambda: {"minute": [], "hour": []}
        )

    async def dispatch(self, request: Request, call_next: Callable):
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        current_time = time.time()

        # Check and update rate limits
        if not self._check_rate_limit(client_ip, current_time):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please slow down your requests.",
                headers={"Retry-After": "60"},
            )

        response = await call_next(request)
        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP, handling proxies."""
        # Check X-Forwarded-For header first (for proxied requests)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"

    def _check_rate_limit(self, client_ip: str, current_time: float) -> bool:
        """Check if request is within rate limits."""
        counts = self.request_counts[client_ip]

        # Clean up old entries and count recent requests
        minute_ago = current_time - 60
        hour_ago = current_time - 3600

        # Filter to recent entries
        counts["minute"] = [(t, c) for t, c in counts["minute"] if t > minute_ago]
        counts["hour"] = [(t, c) for t, c in counts["hour"] if t > hour_ago]

        # Count requests
        minute_count = sum(c for _, c in counts["minute"])
        hour_count = sum(c for _, c in counts["hour"])

        # Check limits
        if minute_count >= self.requests_per_minute:
            return False
        if hour_count >= self.requests_per_hour:
            return False

        # Record this request
        counts["minute"].append((current_time, 1))
        counts["hour"].append((current_time, 1))

        return True


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all API requests for monitoring."""

    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Log request details
        logger.info(
            f"{request.method} {request.url.path} "
            f"status={response.status_code} "
            f"duration={duration_ms:.2f}ms "
            f"client={self._get_client_ip(request)}"
        )

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
