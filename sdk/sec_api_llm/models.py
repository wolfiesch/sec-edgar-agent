from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class ParsedTable:
    """Parsed table with structured data."""
    markdown: str
    structured: List[Dict]
    citation: str
    confidence: str
    metadata: Dict

    def __str__(self) -> str:
        return self.markdown

    def __repr__(self) -> str:
        return f"ParsedTable(citation='{self.citation}', rows={len(self.structured)})"

@dataclass
class Filing:
    """SEC filing metadata."""
    ticker: str
    form_type: str
    filing_date: str
    accession_no: str
    url: str
    citation: str
    sections_available: List[str]
