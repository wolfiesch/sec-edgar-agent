from typing import Optional, Dict
import httpx

from .resources.filings import FilingsResource
from .resources.tables import TablesResource
from .exceptions import SecApiError, NotFoundError, AuthenticationError

class SecClient:
    """
    Python client for SEC API for LLMs.

    Usage:
        client = SecClient(api_key="sk-...")
        table = client.tables.parse(ticker="AAPL", form="10-K", table="segment_info")
        print(table.markdown)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "http://localhost:8000",
        timeout: int = 30
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # HTTP client
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers=self._get_headers()
        )

        # Resources
        self.filings = FilingsResource(self)
        self.tables = TablesResource(self)

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _request(self, method: str, path: str, **kwargs):
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

    def close(self):
        """Close HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
