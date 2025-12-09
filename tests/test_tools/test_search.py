"""Tests for search tools."""

import pytest

from src.tools import registry
from src.tools.search import get_company_info, list_available_forms, search_filings


class TestSearchTools:
    """Tests for search-related tools."""

    def test_tools_registered(self) -> None:
        """Verify search tools are registered."""
        tools = registry.list_tools()
        assert "get_company_info" in tools
        assert "search_filings" in tools
        assert "list_available_forms" in tools

    def test_list_available_forms(self) -> None:
        """Test listing available form types."""
        result = list_available_forms()
        assert "forms" in result
        assert len(result["forms"]) > 0

        # Check for common forms
        form_types = [f["form"] for f in result["forms"]]
        assert "10-K" in form_types
        assert "10-Q" in form_types
        assert "8-K" in form_types


class TestSearchToolsIntegration:
    """Integration tests that hit real SEC API (mark as slow)."""

    @pytest.mark.slow
    def test_get_company_info(self) -> None:
        """Test getting company info for Apple."""
        result = get_company_info("AAPL")

        assert result["ticker"] == "AAPL"
        assert "cik" in result
        assert "name" in result
        assert "Apple" in result["name"]

    @pytest.mark.slow
    def test_search_filings(self) -> None:
        """Test searching for Apple 10-K filings."""
        result = search_filings("AAPL", form_type="10-K", limit=3)

        assert result["company"] == "AAPL"
        assert result["form_type"] == "10-K"
        assert result["count"] == 3
        assert len(result["filings"]) == 3

        # Check filing structure
        filing = result["filings"][0]
        assert "accession_number" in filing
        assert "filing_date" in filing
        assert filing["form_type"] == "10-K"

    @pytest.mark.slow
    def test_search_filings_with_year_filter(self) -> None:
        """Test searching with year filter."""
        result = search_filings(
            "MSFT",
            form_type="10-K",
            start_year=2022,
            end_year=2024,
            limit=5,
        )

        assert result["company"] == "MSFT"
        for filing in result["filings"]:
            year = int(filing["filing_date"][:4])
            assert 2022 <= year <= 2024
