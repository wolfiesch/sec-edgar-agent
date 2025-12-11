from dataclasses import dataclass
from typing import Optional
from edgar import Filing

@dataclass
class Citation:
    """Source citation for SEC filing data."""
    ticker: str
    form_type: str
    filing_date: str
    accession_no: Optional[str] = None
    section: Optional[str] = None
    page: Optional[int] = None
    source_url: Optional[str] = None

    def to_string(self) -> str:
        """
        Format citation as [TICKER FORM YEAR, Section, Page].

        Examples:
            [AAPL 10-K 2024, Item 8, Page 45]
        """
        year = self.filing_date[:4] if self.filing_date else ""
        parts = [f"{self.ticker} {self.form_type} {year}"]

        if self.section:
            parts.append(self.section)
        if self.page:
            parts.append(f"Page {self.page}")

        return f"[{', '.join(parts)}]"

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "citation": self.to_string(),
            "source_url": self.source_url or self._generate_sec_url(),
            "ticker": self.ticker,
            "form_type": self.form_type,
            "filing_date": self.filing_date,
            "section": self.section,
            "page": self.page
        }

    def _generate_sec_url(self) -> Optional[str]:
        """Generate SEC.gov URL for filing."""
        if not self.accession_no:
            return None
        # Format: https://www.sec.gov/cgi-bin/viewer?action=view&accession_number=...
        # Newer edgar URL might differ, but viewer/archives works.
        # Classic Viewer URL
        return f"https://www.sec.gov/cgi-bin/viewer?action=view&accession_number={self.accession_no}"

def create_citation_from_filing(
    filing: Filing,
    section: Optional[str] = None,
    page: Optional[int] = None,
    ticker: Optional[str] = None
) -> Citation:
    """Helper to create citation from edgar.Filing object."""
    # Handle case where filing might not have ticker attribute
    ticker_val = ticker or getattr(filing, "ticker", None)
    if not ticker_val:
        # Fallback or error? For now assume it's passed or present.
        # If filing object really doesn't have it, we need it passed.
        ticker_val = "UNKNOWN"

    return Citation(
        ticker=ticker_val,
        form_type=filing.form,
        filing_date=str(filing.filing_date),
        accession_no=filing.accession_no,
        section=section,
        page=page,
        source_url=filing.url  # edgartools usually provides a URL
    )
