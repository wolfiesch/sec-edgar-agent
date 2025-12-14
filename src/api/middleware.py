"""API middleware for authentication and rate limiting."""

import logging
import time
import uuid
from collections import defaultdict
from collections.abc import Callable

from fastapi import HTTPException, Request, Response, Security
from fastapi.responses import JSONResponse
from fastapi.security.api_key import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

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
        app: Callable,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
    ):
        """Configure rate limits and tracking structures."""
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        # Track request counts per IP: {ip: {"minute": [(timestamp, count)], "hour": [(timestamp, count)]}}
        self.request_counts: dict[str, dict[str, list[tuple[float, int]]]] = defaultdict(
            lambda: {"minute": [], "hour": []}
        )

    def check_rate_limit(self, client_ip: str) -> bool:
        """Check if request is within rate limits and record it."""
        current_time = time.time()
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

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Check rate limit and process request."""
        client_ip = get_client_ip(request)

        if not self.check_rate_limit(client_ip):
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please try again later."},
            )

        return await call_next(request)


def get_client_ip(request: Request) -> str:
    """Extract client IP."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all API requests for monitoring."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process and log the request and response."""
        request_id = str(uuid.uuid4())
        start_time = time.time()

        # Log request
        client_ip = get_client_ip(request)
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": client_ip,
            }
        )

        try:
            response = await call_next(request)

            # Log successful response
            process_time = (time.time() - start_time) * 1000
            logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "process_time_ms": f"{process_time:.2f}",
                }
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as e:
            # Log error
            process_time = (time.time() - start_time) * 1000
            logger.error(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "process_time_ms": f"{process_time:.2f}",
                }
            )
            raise e
