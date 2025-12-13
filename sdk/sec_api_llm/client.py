"""Client utilities for interacting with the SEC EDGAR Agent API."""

import os
from typing import Any

import httpx

from .exceptions import AuthenticationError, NotFoundError, SecApiError
from .resources.filings import FilingsResource
from .resources.search import SearchResource
from .resources.tables import TablesResource


class SecClient:
    """
    Main client for SEC Edgar Agent API.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "http://localhost:8000/api/v1"
    ):
        """Initialize the client with optional API key and base URL."""
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.getenv("SEC_API_KEY")

        # HTTP client
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"X-API-Key": self.api_key} if self.api_key else {},
            timeout=60.0
        )

        # Resources
        self.filings = FilingsResource(self)
        self.tables = TablesResource(self)
        self.search = SearchResource(self)

    def _get_headers(self) -> dict[str, str]:
        """Build default headers including auth if available."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        """Make HTTP request with error handling."""
        try:
            response = self._client.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise NotFoundError(f"Resource not found: {e.response.text}")
            elif e.response.status_code == 401:
                raise AuthenticationError(f"Authentication failed: {e.response.text}")
            else:
                raise SecApiError(f"API error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise SecApiError(f"Request failed: {str(e)}")

    def close(self) -> None:
        """Close HTTP client."""
        self._client.close()

    def __enter__(self) -> "SecClient":
        """Allow usage as a context manager."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Close the underlying HTTP client on context exit."""
        self.close()
