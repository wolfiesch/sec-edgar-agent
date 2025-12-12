"""Citation utilities for SEC filing references."""

from datetime import date
from typing import Any

from edgar import Filing

from src.data.models import Citation


def create_citation(
    ticker: str,
    form_type: str,
    filing_date: date,
    accession_number: str,
    section: str | None = None,
    page: int | None = None,
) -> Citation:
    """
    Create a citation with normalized ticker.

    Args:
        ticker: Company ticker symbol (will be uppercased)
        form_type: Form type (10-K, 10-Q, etc.)
        filing_date: Filing date
        accession_number: SEC accession number
        section: Optional section name
        page: Optional page number

    Returns:
        Citation object
    """
    return Citation(
        ticker=ticker.upper(),
        form_type=form_type,
        filing_date=filing_date,
        accession_number=accession_number,
        section=section,
        page=page,
    )


def create_citation_from_filing(
    filing: Filing,
    section: str | None = None,
    page: int | None = None,
    ticker: str | None = None,
) -> Citation:
    """
    Helper to create citation from edgar.Filing object.

    Args:
        filing: Edgar Filing object
        section: Optional section name
        page: Optional page number
        ticker: Optional ticker override (if filing doesn't have it)

    Returns:
        Citation object
    """
    # Handle case where filing might not have ticker attribute
    ticker_val = ticker or getattr(filing, "ticker", None)
    if not ticker_val:
        ticker_val = "UNKNOWN"

    # Convert filing_date to date object if it's a string
    filing_date_val = filing.filing_date
    if isinstance(filing_date_val, str):
        filing_date_val = date.fromisoformat(filing_date_val)

    return Citation(
        ticker=ticker_val.upper() if ticker_val else "UNKNOWN",
        form_type=filing.form,
        filing_date=filing_date_val,
        accession_number=filing.accession_no,
        section=section,
        page=page,
    )


def format_citation(citation: Citation) -> str:
    """
    Format a single citation as string.

    Format: [TICKER, FORM, YEAR] or [TICKER, FORM, YEAR, Section] or [TICKER, FORM, YEAR, Section, p.X]

    Args:
        citation: Citation object

    Returns:
        Formatted citation string

    Examples:
        >>> citation = Citation(ticker="AAPL", form_type="10-K", filing_date=date(2024, 10, 31), accession_number="...")
        >>> format_citation(citation)
        '[AAPL, 10-K, 2024]'
    """
    return str(citation)


def format_citations(citations: list[Citation]) -> str:
    """
    Format multiple citations with deduplication.

    Args:
        citations: List of Citation objects

    Returns:
        Formatted citations string (comma-separated, deduplicated)

    Examples:
        >>> citations = [Citation(...), Citation(...)]
        >>> format_citations(citations)
        '[AAPL, 10-K, 2024], [MSFT, 10-Q, 2024, Risk Factors]'
    """
    if not citations:
        return ""

    # Deduplicate by string representation
    unique_citations = []
    seen = set()

    for citation in citations:
        citation_str = str(citation)
        if citation_str not in seen:
            seen.add(citation_str)
            unique_citations.append(citation_str)

    return ", ".join(unique_citations)


def citation_to_url(citation: Citation) -> str:
    """
    Convert citation to SEC EDGAR URL.

    Args:
        citation: Citation object

    Returns:
        SEC.gov URL to the filing

    Examples:
        >>> citation = Citation(ticker="AAPL", ..., accession_number="0000320193-24-000123")
        >>> citation_to_url(citation)
        'https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/...'
    """
    # Extract CIK from accession number (first 10 digits)
    # Format: XXXXXXXXXX-YY-ZZZZZZ where X is CIK with leading zeros
    accession_no = citation.accession_number.replace("-", "")
    cik = citation.accession_number.split("-")[0].lstrip("0")  # Remove leading zeros

    # SEC URL format: https://www.sec.gov/Archives/edgar/data/{CIK}/{ACCESSION}/{PRIMARY_DOC}
    # For now, just return the data directory URL since we don't have primary doc info
    return f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_no}/"


def merge_citations(*citation_lists: list[Citation]) -> list[Citation]:
    """
    Merge multiple citation lists with deduplication.

    Deduplication is based on all fields (ticker, form, date, section, page).

    Args:
        *citation_lists: Variable number of citation lists to merge

    Returns:
        Merged and deduplicated list of citations

    Examples:
        >>> list1 = [Citation(...)]
        >>> list2 = [Citation(...)]
        >>> merged = merge_citations(list1, list2)
    """
    merged = []
    seen: set[tuple[Any, ...]] = set()

    for citation_list in citation_lists:
        for citation in citation_list:
            # Create a hashable key from citation fields
            key = (
                citation.ticker,
                citation.form_type,
                citation.filing_date,
                citation.section,
                citation.page,
                citation.accession_number,
            )

            if key not in seen:
                seen.add(key)
                merged.append(citation)

    return merged
