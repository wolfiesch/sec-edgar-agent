from pydantic import BaseModel
from typing import Optional, List, Dict

class Citation(BaseModel):
    """Source citation for data."""
    ticker: str
    form_type: str
    filing_date: str
    section: Optional[str] = None
    page: Optional[int] = None

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
    structured: List[Dict]
    citation: str
    confidence: str
    metadata: Dict

class FilingResponse(BaseModel):
    """Filing metadata response."""
    ticker: str
    form_type: str
    filing_date: str
    accession_no: str
    url: str
    citation: str
    sections_available: List[str]
