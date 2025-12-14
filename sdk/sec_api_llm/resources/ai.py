"""AI-related resources (search, chat, ingest) for the SDK."""

from typing import Any

from .models import ChatMessage, ChatResponse, SearchResponse


class SearchResource:
    """Wrapper around semantic search endpoints."""

    def __init__(self, client: Any):
        """Store reference to the shared API client."""
        self._client = client

    def query(self, query: str, ticker: str | None = None, section: str | None = None, limit: int = 5) -> SearchResponse:
        """Search for relevant filing sections."""
        payload = {
            "query": query,
            "ticker": ticker,
            "section": section,
            "limit": limit
        }
        data = self._client._post("search", json=payload)
        return SearchResponse(**data)

class ChatResource:
    """Resource for conversational access to filings."""

    def __init__(self, client: Any):
        """Store reference to the shared API client."""
        self._client = client

    def create(self, messages: list[dict[str, Any] | ChatMessage], ticker: str | None = None) -> ChatResponse:
        """Chat with the SEC data."""
        # Convert dicts to ChatMessage if needed
        msgs = []
        for m in messages:
            if isinstance(m, dict):
                msgs.append(ChatMessage(**m))
            else:
                msgs.append(m)

        payload = {
            "messages": [m.model_dump() for m in msgs],
            "ticker": ticker
        }
        data = self._client._post("chat", json=payload)
        return ChatResponse(**data)

class IngestResource:
    """Resource for ingestion jobs."""

    def __init__(self, client: Any):
        """Store reference to the shared API client."""
        self._client = client

    def trigger(self, ticker: str, form_type: str, year: int) -> dict[str, Any]:
        """Trigger ingestion job."""
        payload = {
            "ticker": ticker,
            "form_type": form_type,
            "year": year
        }
        # Cast to expect dict return from _post
        return dict(self._client._post("ingest", json=payload))

    def get(self, job_id: int) -> dict[str, Any]:
        """Get job status."""
        # Cast to expect dict return from _get
        return dict(self._client._get(f"ingest/{job_id}"))
