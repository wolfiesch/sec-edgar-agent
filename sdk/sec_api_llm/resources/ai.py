
from .models import ChatMessage, ChatResponse, SearchResponse


class SearchResource:
    def __init__(self, client):
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
    def __init__(self, client):
        self._client = client

    def create(self, messages: list[dict | ChatMessage], ticker: str | None = None) -> ChatResponse:
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
    def __init__(self, client):
        self._client = client

    def trigger(self, ticker: str, form_type: str, year: int) -> dict:
        """Trigger ingestion job."""
        payload = {
            "ticker": ticker,
            "form_type": form_type,
            "year": year
        }
        return self._client._post("ingest", json=payload)

    def get(self, job_id: int) -> dict:
        """Get job status."""
        return self._client._get(f"ingest/{job_id}")
