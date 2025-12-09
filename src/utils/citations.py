"""Citation generation and formatting utilities."""

from datetime import date

from src.data.models import Citation


def format_citation(citation: Citation) -> str:
    """
    Format a citation for display.

    Examples:
        [AAPL 10-K 2024]
        [MSFT 10-K 2024, Risk Factors]
        [GOOGL 10-K 2024, Item 7, p.45]
    """
    return str(citation)


def format_citations(citations: list[Citation]) -> str:
    """Format multiple citations."""
    if not citations:
        return ""

    unique = {str(c): c for c in citations}
    return " ".join(format_citation(c) for c in unique.values())


def create_citation(
    ticker: str,
    form_type: str,
    filing_date: date,
    accession_number: str,
    section: str | None = None,
    page: int | None = None,
) -> Citation:
    """Create a new citation."""
    return Citation(
        ticker=ticker.upper(),
        form_type=form_type,
        filing_date=filing_date,
        accession_number=accession_number,
        section=section,
        page=page,
    )


def citation_to_url(citation: Citation) -> str:
    """
    Convert a citation to a SEC EDGAR URL.

    Returns URL to the filing on SEC website.
    """
    # Format accession number for URL (remove dashes)
    acc_num = citation.accession_number.replace("-", "")

    # Extract CIK from accession number if possible, otherwise use ticker
    # Accession format: NNNNNNNNNN-YY-NNNNNN where first 10 digits are CIK
    if len(citation.accession_number) >= 10:
        cik = citation.accession_number[:10].lstrip("0")
    else:
        cik = citation.ticker  # Fallback

    return f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_num}"


def merge_citations(
    *citation_lists: list[Citation],
) -> list[Citation]:
    """Merge multiple citation lists, removing duplicates."""
    seen: set[str] = set()
    result: list[Citation] = []

    for citations in citation_lists:
        for citation in citations:
            key = f"{citation.ticker}:{citation.accession_number}:{citation.section}"
            if key not in seen:
                seen.add(key)
                result.append(citation)

    return result
