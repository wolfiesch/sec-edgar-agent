"""Response models returned by the API."""
from pydantic import BaseModel


class Citation(BaseModel):
    """Source citation for data."""
    ticker: str
    form_type: str
    filing_date: str
    section: str | None = None
    page: int | None = None

    def to_string(self) -> str:
        """Format as [TICKER FORM YEAR, Section, Page]"""
        year = self.filing_date[:4] if self.filing_date else ""
        parts = [f"{self.ticker} {self.form_type} {year}"]
        if self.section:
            parts.append(self.section)
        if self.page:
            parts.append(f"Page {self.page}")
        return f"[{', '.join(parts)}]"

class ParsedTableResponse(BaseModel):
    """Response containing parsed table data."""
    markdown: str
    structured: list[dict]
    citation: str
    confidence: str
    section: str | None = None  # e.g., "Item 8"
    metadata: dict

class FilingResponse(BaseModel):
    """Filing metadata response."""
    ticker: str
    form_type: str
    filing_date: str
    accession_no: str
    url: str
    citation: str
    sections_available: list[str]


class SearchResult(BaseModel):
    """Single search result item."""
    content: str
    citation: str
    metadata: dict
    distance: float | None = None


class SearchResponse(BaseModel):
    """Response model for search endpoint."""
    results: list[SearchResult]
    total: int
