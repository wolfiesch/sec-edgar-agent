"""Table parsing resource for the SDK."""
from typing import TYPE_CHECKING

from ..models import ParsedTable

if TYPE_CHECKING:
    from ..client import SecClient

class TablesResource:
    """Tables resource for parsing SEC tables."""

    def __init__(self, client: "SecClient"):
        """Store the API client used for HTTP calls."""
        self._client = client

    def parse(
        self,
        ticker: str,
        form: str,
        table: str,
        year: int | None = None
    ) -> ParsedTable:
        """
        Parse a table from SEC filing.

        Args:
            ticker: Stock ticker (e.g., "AAPL")
            form: Form type (e.g., "10-K")
            table: Table identifier (e.g., "segment_information")
            year: Filing year (default: latest)

        Returns:
            ParsedTable with markdown, structured data, and citation
        """
        data = {
            "ticker": ticker,
            "form_type": form,
            "table_name": table,
            "year": year
        }
        # Filter None values
        data = {k: v for k, v in data.items() if v is not None}

        response = self._client._request(
            "POST",
            "/tables/parse",
            json=data
        )
        return ParsedTable(**response)
