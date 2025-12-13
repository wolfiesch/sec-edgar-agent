"""Filings resource wrapper for the SEC API LLM SDK."""
from typing import TYPE_CHECKING

from ..models import Filing

if TYPE_CHECKING:
    from ..client import SecClient

class FilingsResource:
    """Resource for accessing SEC filings."""

    def __init__(self, client: "SecClient"):
        """Store the client used to issue HTTP requests."""
        self._client = client

    def get(
        self,
        ticker: str,
        form: str,
        year: int | None = None
    ) -> Filing:
        """
        Get metadata for a specific filing.

        Args:
            ticker: Stock ticker
            form: Form type (e.g., "10-K")
            year: Optional year
        """
        params = {}
        if year:
            params["year"] = int(year)

        response = self._client._request(
            "GET",
            f"/filings/{ticker}/{form}",
            params=params
        )
        return Filing(**response)

    def list(
        self,
        ticker: str,
        form: str | None = None,
        limit: int = 10
    ) -> list[Filing]:
        """
        List filings for a company.

        Args:
            ticker: Stock ticker
            form: Optional form type filter
            limit: Maximum number of results

        Returns:
            List of Filing objects
        """
        params = {"limit": limit}
        if form:
            params["form"] = form

        response = self._client._request(
            "GET",
            f"/filings/{ticker}",
            params=params
        )
        # API returns a list directly or wrapped in a response
        filings_data = response if isinstance(response, list) else response.get("filings", [])
        return [Filing(**f) for f in filings_data]
