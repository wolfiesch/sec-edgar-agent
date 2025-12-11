from src.utils.citations import Citation

def test_citation_formatting():
    """Test citation string formatting."""
    citation = Citation(
        ticker="AAPL",
        form_type="10-K",
        filing_date="2024-11-01"
    )
    assert citation.to_string() == "[AAPL 10-K 2024]"

    citation_section = Citation(
        ticker="MSFT",
        form_type="10-Q",
        filing_date="2024-10-30",
        section="Item 2"
    )
    assert citation_section.to_string() == "[MSFT 10-Q 2024, Item 2]"

    citation_page = Citation(
        ticker="NVDA",
        form_type="8-K",
        filing_date="2024-09-01",
        page=5
    )
    assert citation_page.to_string() == "[NVDA 8-K 2024, Page 5]"
