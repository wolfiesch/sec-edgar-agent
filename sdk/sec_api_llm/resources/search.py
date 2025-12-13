"""Search resource helpers for the SDK."""
from typing import TYPE_CHECKING

from ..models import SearchResponse, SearchResult

if TYPE_CHECKING:
    from ..client import SecClient


class SearchResource:
    """Resource for searching SEC filings."""

    def __init__(self, client: "SecClient"):
        """Store the API client used for requests."""
        self._client = client

    def semantic(
        self,
        query: str,
        ticker: str | None = None,
        section: str | None = None,
        limit: int = 5
    ) -> SearchResponse:
        """
        Semantic search across SEC filings using embeddings.

        Args:
            query: Natural language search query
            ticker: Optional ticker to filter by
            section: Optional section to filter by (e.g., "Item 1A")
            limit: Maximum results (1-20)

        Returns:
            SearchResponse with results and citations

        Example:
            >>> results = client.search.semantic("risk factors mentioning China")
            >>> for r in results:
            ...     print(r.citation, r.content[:100])
        """
        data = {
            "query": query,
            "ticker": ticker,
            "section": section,
            "limit": min(max(limit, 1), 20)
        }
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}

        response = self._client._request(
            "POST",
            "/search/",
            json=data
        )

        results = [SearchResult(**r) for r in response.get("results", [])]
        return SearchResponse(
            results=results,
            total=response.get("total", len(results))
        )

    def full_text(
        self,
        query: str,
        form_types: list[str] | None = None,
        limit: int = 20
    ) -> list[dict]:
        """
        Full-text search across all SEC filings using SEC's EFTS API.

        Args:
            query: Search query (supports boolean: AND, OR, NOT, "exact phrase")
            form_types: Optional list of form types (e.g., ["10-K", "10-Q"])
            limit: Maximum results (1-100)

        Returns:
            List of filing metadata dicts

        Example:
            >>> results = client.search.full_text('"artificial intelligence"', form_types=["10-K"])
        """
        data = {
            "query": query,
            "form_types": form_types,
            "limit": min(max(limit, 1), 100)
        }
        data = {k: v for k, v in data.items() if v is not None}

        response = self._client._request(
            "POST",
            "/search/full-text",
            json=data
        )

        results = response.get("results", [])
        if isinstance(results, list):
            return results
        return []
