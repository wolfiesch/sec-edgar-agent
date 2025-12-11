from typing import TYPE_CHECKING

from ..models import Filing

if TYPE_CHECKING:
    from ..client import SecClient

class FilingsResource:
    """Resource for accessing SEC filings."""

    def __init__(self, client: "SecClient"):
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
            params["year"] = year

        response = self._client._request(
            "GET",
            f"/api/v1/filings/{ticker}/{form}",
            params=params
        )
        return Filing(**response)
