"""Tests for citation utilities."""

from datetime import date

from src.data.models import Citation
from src.utils.citations import (
    citation_to_url,
    create_citation,
    format_citation,
    format_citations,
    merge_citations,
)


class TestCitationCreation:
    """Tests for creating citations."""

    def test_create_citation_minimal(self) -> None:
        """Test creating a citation with minimal info."""
        citation = create_citation(
            ticker="aapl",
            form_type="10-K",
            filing_date=date(2024, 10, 31),
            accession_number="0000320193-24-000123",
        )

        assert citation.ticker == "AAPL"  # Should be uppercase
        assert citation.form_type == "10-K"
        assert citation.filing_date == date(2024, 10, 31)
        assert citation.accession_number == "0000320193-24-000123"
        assert citation.section is None
        assert citation.page is None

    def test_create_citation_with_section(self) -> None:
        """Test creating a citation with section."""
        citation = create_citation(
            ticker="MSFT",
            form_type="10-Q",
            filing_date=date(2024, 7, 30),
            accession_number="0000789019-24-000456",
            section="Risk Factors",
        )

        assert citation.ticker == "MSFT"
        assert citation.section == "Risk Factors"

    def test_create_citation_with_page(self) -> None:
        """Test creating a citation with page number."""
        citation = create_citation(
            ticker="GOOGL",
            form_type="10-K",
            filing_date=date(2024, 2, 1),
            accession_number="0001652044-24-000001",
            section="Management's Discussion",
            page=42,
        )

        assert citation.page == 42
        assert citation.section == "Management's Discussion"


class TestCitationFormatting:
    """Tests for formatting citations."""

    def test_format_citation_minimal(self) -> None:
        """Test formatting a minimal citation."""
        citation = Citation(
            ticker="AAPL",
            form_type="10-K",
            filing_date=date(2024, 10, 31),
            accession_number="0000320193-24-000123",
        )

        result = format_citation(citation)
        assert result == "[AAPL, 10-K, 2024]"

    def test_format_citation_with_section(self) -> None:
        """Test formatting with section."""
        citation = Citation(
            ticker="MSFT",
            form_type="10-Q",
            filing_date=date(2024, 7, 30),
            accession_number="0000789019-24-000456",
            section="Risk Factors",
        )

        result = format_citation(citation)
        assert result == "[MSFT, 10-Q, 2024, Risk Factors]"

    def test_format_citation_with_section_and_page(self) -> None:
        """Test formatting with section and page."""
        citation = Citation(
            ticker="GOOGL",
            form_type="10-K",
            filing_date=date(2024, 2, 1),
            accession_number="0001652044-24-000001",
            section="Item 7",
            page=45,
        )

        result = format_citation(citation)
        assert result == "[GOOGL, 10-K, 2024, Item 7, p.45]"

    def test_format_citations_empty(self) -> None:
        """Test formatting empty citation list."""
        result = format_citations([])
        assert result == ""

    def test_format_citations_single(self) -> None:
        """Test formatting single citation."""
        citations = [
            Citation(
                ticker="AAPL",
                form_type="10-K",
                filing_date=date(2024, 10, 31),
                accession_number="0000320193-24-000123",
            )
        ]

        result = format_citations(citations)
        assert result == "[AAPL, 10-K, 2024]"

    def test_format_citations_multiple(self) -> None:
        """Test formatting multiple citations."""
        citations = [
            Citation(
                ticker="AAPL",
                form_type="10-K",
                filing_date=date(2024, 10, 31),
                accession_number="0000320193-24-000123",
            ),
            Citation(
                ticker="MSFT",
                form_type="10-Q",
                filing_date=date(2024, 7, 30),
                accession_number="0000789019-24-000456",
                section="Risk Factors",
            ),
        ]

        result = format_citations(citations)
        assert "[AAPL, 10-K, 2024]" in result
        assert "[MSFT, 10-Q, 2024, Risk Factors]" in result

    def test_format_citations_deduplication(self) -> None:
        """Test that duplicate citations are deduplicated."""
        citations = [
            Citation(
                ticker="AAPL",
                form_type="10-K",
                filing_date=date(2024, 10, 31),
                accession_number="0000320193-24-000123",
            ),
            Citation(
                ticker="AAPL",
                form_type="10-K",
                filing_date=date(2024, 10, 31),
                accession_number="0000320193-24-000123",
            ),
        ]

        result = format_citations(citations)
        # Should only appear once
        assert result.count("[AAPL, 10-K, 2024]") == 1


class TestCitationToUrl:
    """Tests for converting citations to URLs."""

    def test_citation_to_url_basic(self) -> None:
        """Test converting citation to SEC URL."""
        citation = Citation(
            ticker="AAPL",
            form_type="10-K",
            filing_date=date(2024, 10, 31),
            accession_number="0000320193-24-000123",
        )

        url = citation_to_url(citation)
        assert url.startswith("https://www.sec.gov/Archives/edgar/data/")
        assert "320193" in url  # CIK without leading zeros
        assert "000032019324000123" in url  # Accession without dashes

    def test_citation_to_url_removes_dashes(self) -> None:
        """Test that dashes are removed from accession number."""
        citation = Citation(
            ticker="MSFT",
            form_type="10-Q",
            filing_date=date(2024, 7, 30),
            accession_number="0000789019-24-000456",
        )

        url = citation_to_url(citation)
        assert "-" not in url.split("/")[-1]  # No dashes in accession part

    def test_citation_to_url_extracts_cik(self) -> None:
        """Test that CIK is properly extracted from accession number."""
        citation = Citation(
            ticker="GOOGL",
            form_type="10-K",
            filing_date=date(2024, 2, 1),
            accession_number="0001652044-24-000001",
        )

        url = citation_to_url(citation)
        # Should extract CIK 1652044 from accession
        assert "/1652044/" in url


class TestMergeCitations:
    """Tests for merging citation lists."""

    def test_merge_empty_lists(self) -> None:
        """Test merging empty lists."""
        result = merge_citations([], [])
        assert result == []

    def test_merge_single_list(self) -> None:
        """Test merging a single list."""
        citations = [
            Citation(
                ticker="AAPL",
                form_type="10-K",
                filing_date=date(2024, 10, 31),
                accession_number="0000320193-24-000123",
            )
        ]

        result = merge_citations(citations)
        assert len(result) == 1
        assert result[0].ticker == "AAPL"

    def test_merge_multiple_lists(self) -> None:
        """Test merging multiple lists."""
        list1 = [
            Citation(
                ticker="AAPL",
                form_type="10-K",
                filing_date=date(2024, 10, 31),
                accession_number="0000320193-24-000123",
            )
        ]
        list2 = [
            Citation(
                ticker="MSFT",
                form_type="10-Q",
                filing_date=date(2024, 7, 30),
                accession_number="0000789019-24-000456",
            )
        ]

        result = merge_citations(list1, list2)
        assert len(result) == 2
        tickers = {c.ticker for c in result}
        assert tickers == {"AAPL", "MSFT"}

    def test_merge_removes_duplicates(self) -> None:
        """Test that duplicates are removed during merge."""
        citation = Citation(
            ticker="AAPL",
            form_type="10-K",
            filing_date=date(2024, 10, 31),
            accession_number="0000320193-24-000123",
        )
        list1 = [citation]
        list2 = [citation]

        result = merge_citations(list1, list2)
        assert len(result) == 1

    def test_merge_keeps_different_sections(self) -> None:
        """Test that same filing with different sections are kept separate."""
        citation1 = Citation(
            ticker="AAPL",
            form_type="10-K",
            filing_date=date(2024, 10, 31),
            accession_number="0000320193-24-000123",
            section="Risk Factors",
        )
        citation2 = Citation(
            ticker="AAPL",
            form_type="10-K",
            filing_date=date(2024, 10, 31),
            accession_number="0000320193-24-000123",
            section="Management Discussion",
        )

        result = merge_citations([citation1], [citation2])
        # Different sections should be kept separate
        assert len(result) == 2
