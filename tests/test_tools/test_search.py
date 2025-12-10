"""Tests for search tools."""

from datetime import date
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.data.models import Company, Filing
from src.tools import registry
from src.tools.search import get_company_info, list_available_forms, search_filings


class TestSearchToolsRegistry:
    """Tests for search tool registration."""

    def test_tools_registered(self) -> None:
        """Verify search tools are registered."""
        tools = registry.list_tools()
        assert "get_company_info" in tools
        assert "search_filings" in tools
        assert "list_available_forms" in tools


class TestGetCompanyInfo:
    """Tests for get_company_info function."""

    @patch("src.tools.search.get_edgar_client")
    def test_get_company_info_success(self, mock_get_client: Mock) -> None:
        """Test successfully getting company information."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_company = Company(
            cik="0000320193",
            ticker="AAPL",
            name="Apple Inc",
            sic="3571",
            sic_description="Electronic Computers",
            exchange="NASDAQ",
        )
        mock_client.get_company.return_value = mock_company

        result = get_company_info("AAPL")

        assert result["cik"] == "0000320193"
        assert result["ticker"] == "AAPL"
        assert result["name"] == "Apple Inc"
        assert result["sic"] == "3571"
        assert result["sic_description"] == "Electronic Computers"
        assert result["exchange"] == "NASDAQ"

        mock_client.get_company.assert_called_once_with("AAPL")

    @patch("src.tools.search.get_edgar_client")
    def test_get_company_info_with_none_fields(self, mock_get_client: Mock) -> None:
        """Test company info with optional fields set to None."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_company = Company(
            cik="123",
            ticker="TEST",
            name="Test Corp",
            sic=None,
            sic_description=None,
            exchange=None,
        )
        mock_client.get_company.return_value = mock_company

        result = get_company_info("TEST")

        assert result["sic"] is None
        assert result["sic_description"] is None
        assert result["exchange"] is None


class TestSearchFilings:
    """Tests for search_filings function."""

    @patch("src.tools.search.get_edgar_client")
    def test_search_filings_basic(self, mock_get_client: Mock) -> None:
        """Test basic filing search."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        company = Company(
            cik="0000320193",
            ticker="AAPL",
            name="Apple Inc",
            sic=None,
            sic_description=None,
            exchange=None,
        )

        filing = Filing(
            accession_number="0000320193-23-000106",
            form_type="10-K",
            filing_date=date(2023, 10, 27),
            report_date=date(2023, 9, 30),
            company=company,
            primary_document="aapl-20230930.htm",
            url="https://www.sec.gov/...",
        )

        mock_client.get_filings.return_value = [filing]

        result = search_filings("AAPL", form_type="10-K", limit=5)

        assert result["company"] == "AAPL"
        assert result["form_type"] == "10-K"
        assert result["count"] == 1
        assert len(result["filings"]) == 1
        assert result["filings"][0]["accession_number"] == "0000320193-23-000106"
        assert result["filings"][0]["filing_date"] == "2023-10-27"
        assert result["filings"][0]["report_date"] == "2023-09-30"
        assert result["filings"][0]["form_type"] == "10-K"
        assert "citations" in result

        # Verify client was called without date filters
        mock_client.get_filings.assert_called_once_with(
            ticker="AAPL",
            form_type="10-K",
            limit=5,
            start_date=None,
            end_date=None,
        )

    @patch("src.tools.search.get_edgar_client")
    def test_search_filings_with_year_filters(self, mock_get_client: Mock) -> None:
        """Test filing search with year filters."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_client.get_filings.return_value = []

        search_filings(
            "MSFT",
            form_type="10-Q",
            limit=10,
            start_year=2022,
            end_year=2024,
        )

        # Verify date conversion
        mock_client.get_filings.assert_called_once_with(
            ticker="MSFT",
            form_type="10-Q",
            limit=10,
            start_date=date(2022, 1, 1),
            end_date=date(2024, 12, 31),
        )

    @patch("src.tools.search.get_edgar_client")
    def test_search_filings_empty_results(self, mock_get_client: Mock) -> None:
        """Test filing search with no results."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_client.get_filings.return_value = []

        result = search_filings("INVALID", form_type="10-K")

        assert result["company"] == "INVALID"
        assert result["count"] == 0
        assert len(result["filings"]) == 0
        assert result["citations"] == []

    @patch("src.tools.search.get_edgar_client")
    def test_search_filings_multiple_results(self, mock_get_client: Mock) -> None:
        """Test filing search returning multiple results."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        company = Company(
            cik="0000789019",
            ticker="MSFT",
            name="Microsoft Corp",
            sic=None,
            sic_description=None,
            exchange=None,
        )

        filings = [
            Filing(
                accession_number="0001564590-23-012345",
                form_type="10-Q",
                filing_date=date(2023, 7, 28),
                report_date=date(2023, 6, 30),
                company=company,
                primary_document="msft-20230630.htm",
                url="https://www.sec.gov/1",
            ),
            Filing(
                accession_number="0001564590-23-012346",
                form_type="10-Q",
                filing_date=date(2023, 4, 25),
                report_date=date(2023, 3, 31),
                company=company,
                primary_document="msft-20230331.htm",
                url="https://www.sec.gov/2",
            ),
        ]

        mock_client.get_filings.return_value = filings

        result = search_filings("MSFT", form_type="10-Q", limit=2)

        assert result["count"] == 2
        assert len(result["filings"]) == 2
        assert len(result["citations"]) == 2
        assert result["filings"][0]["filing_date"] == "2023-07-28"
        assert result["filings"][1]["filing_date"] == "2023-04-25"

    @patch("src.tools.search.get_edgar_client")
    def test_search_filings_none_report_date(self, mock_get_client: Mock) -> None:
        """Test filing with None report_date."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        company = Company(
            cik="123",
            ticker="TEST",
            name="Test Corp",
            sic=None,
            sic_description=None,
            exchange=None,
        )

        filing = Filing(
            accession_number="123",
            form_type="8-K",
            filing_date=date(2023, 11, 1),
            report_date=None,  # 8-K may not have report_date
            company=company,
            primary_document="test.htm",
            url="https://www.sec.gov/test",
        )

        mock_client.get_filings.return_value = [filing]

        result = search_filings("TEST", form_type="8-K")

        assert result["filings"][0]["report_date"] is None


class TestListAvailableForms:
    """Tests for list_available_forms function."""

    def test_list_available_forms_structure(self) -> None:
        """Test that list_available_forms returns correct structure."""
        result = list_available_forms()

        assert "forms" in result
        assert isinstance(result["forms"], list)
        assert len(result["forms"]) > 0

        # Check form structure
        for form in result["forms"]:
            assert "form" in form
            assert "description" in form
            assert isinstance(form["form"], str)
            assert isinstance(form["description"], str)

    def test_list_available_forms_contains_common_forms(self) -> None:
        """Test that common SEC forms are included."""
        result = list_available_forms()
        form_types = [f["form"] for f in result["forms"]]

        # Check for most common forms
        assert "10-K" in form_types
        assert "10-Q" in form_types
        assert "8-K" in form_types
        assert "4" in form_types
        assert "DEF 14A" in form_types


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
