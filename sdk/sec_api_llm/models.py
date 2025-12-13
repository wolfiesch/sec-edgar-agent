"""Pydantic models for the SEC API LLM SDK."""

from pydantic import BaseModel
from typing import Any, Iterator

# --- Search ---

class SearchResult(BaseModel):
    """Single search result."""
    content: str
    citation: str
    metadata: dict[str, Any] = {}
    distance: float | None = None

    def __repr__(self) -> str:
        """Return a compact preview of the search result."""
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"SearchResult(citation='{self.citation}', preview='{preview}')"


class SearchResponse(BaseModel):
    """Search response with results."""
    results: list[SearchResult]
    total: int

    def __iter__(self) -> Iterator[SearchResult]:
        """Iterate over the returned search results."""
        return iter(self.results)

    def __len__(self) -> int:
        """Return the number of results."""
        return self.total

    def __repr__(self) -> str:
        """Return a readable summary for debugging."""
        return f"SearchResponse(total={self.total})"

class ChatResponse(BaseModel):
    """Response payload for chat completions."""
    answer: str
    citations: list[str]
    usage: dict

# --- Requests ---

class ChatMessage(BaseModel):
    """Single chat message exchanged with the API."""
    role: str
    content: str

# Existing models...
class ParsedTable(BaseModel):
    """Parsed table data returned from the SEC API."""
    markdown: str
    structured: list[dict]
    citation: str
    confidence: str
    section: str | None = None  # e.g., "Item 8"
    metadata: dict = {}

    def __str__(self) -> str:
        """Return the markdown table for display."""
        return self.markdown

    def __repr__(self) -> str:
        """Return a concise identifier for the parsed table."""
        return f"ParsedTable(citation='{self.citation}', section='{self.section}', rows={len(self.structured)})"

class Filing(BaseModel):
    """SEC filing metadata."""
    ticker: str
    form_type: str
    filing_date: str
    accession_no: str
    url: str
    citation: str
    sections_available: list[str]

    def __repr__(self) -> str:
        """Return a short summary of the filing."""
        return f"Filing(ticker='{self.ticker}', form='{self.form_type}', date='{self.filing_date}')"
