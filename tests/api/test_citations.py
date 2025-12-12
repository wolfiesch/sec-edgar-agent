from datetime import date

from src.data.models import Citation


def test_citation_formatting():
    """Test citation string formatting."""
    citation = Citation(
        ticker="AAPL",
        form_type="10-K",
        filing_date=date(2024, 11, 1),
        accession_number="0000320193-24-000123",
    )
    assert str(citation) == "[AAPL, 10-K, 2024]"

    citation_section = Citation(
        ticker="MSFT",
        form_type="10-Q",
        filing_date=date(2024, 10, 30),
        accession_number="0000789019-24-000456",
        section="Item 2",
    )
    assert str(citation_section) == "[MSFT, 10-Q, 2024, Item 2]"

    citation_page = Citation(
        ticker="NVDA",
        form_type="8-K",
        filing_date=date(2024, 9, 1),
        accession_number="0001045810-24-000789",
        page=5,
    )
    assert str(citation_page) == "[NVDA, 8-K, 2024, p.5]"
