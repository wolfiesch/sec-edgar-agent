"""Tests for filing fetch tools."""

from datetime import date
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.tools import registry
from src.tools.fetch import (
    get_filing_document,
    get_filing_exhibits,
    get_filing_section,
)


class TestFetchToolsRegistry:
    """Tests for fetch tool registration."""

    def test_tools_registered(self) -> None:
        """Verify all fetch tools are registered."""
        tools = registry.list_tools()
        assert "get_filing_document" in tools
        assert "get_filing_section" in tools
        assert "get_filing_exhibits" in tools


class TestGetFilingDocument:
    """Tests for get_filing_document function."""

    @patch("src.tools.fetch.get_edgar_client")
    def test_get_filing_document_success(self, mock_get_client: Mock) -> None:
        """Test successfully fetching a filing document."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock filing object
        mock_filing = MagicMock()
        mock_filing.form = "10-K"
        mock_filing.filing_date = date(2023, 10, 27)
        mock_filing.text.return_value = "This is the full text of the 10-K filing with detailed financial information."

        mock_client.get_filing_by_accession.return_value = mock_filing

        result = get_filing_document("AAPL", "0000320193-23-000106", 200)

        assert result["success"] is True
        assert result["ticker"] == "AAPL"
        assert result["form_type"] == "10-K"
        assert result["filing_date"] == "2023-10-27"
        assert result["accession_number"] == "0000320193-23-000106"
        assert "This is the full text" in result["content"]
        assert result["truncated"] is False
        assert "citations" in result

    @patch("src.tools.fetch.get_edgar_client")
    def test_get_filing_document_truncation(self, mock_get_client: Mock) -> None:
        """Test document truncation for large filings."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Create a large document
        large_text = "A" * 100000
        mock_filing = MagicMock()
        mock_filing.form = "10-K"
        mock_filing.filing_date = date(2023, 10, 27)
        mock_filing.text.return_value = large_text

        mock_client.get_filing_by_accession.return_value = mock_filing

        result = get_filing_document("AAPL", "0000320193-23-000106", max_length=50000)

        assert result["success"] is True
        assert result["truncated"] is True
        assert len(result["content"]) <= 50025  # 50000 + truncation message (with margin)
        assert "[... truncated ...]" in result["content"]
        assert result["total_length"] == 100000

    @patch("src.tools.fetch.get_edgar_client")
    def test_get_filing_document_default_max_length(self, mock_get_client: Mock) -> None:
        """Test using default max_length parameter."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_filing = MagicMock()
        mock_filing.form = "10-Q"
        mock_filing.filing_date = date(2023, 7, 28)
        mock_filing.text.return_value = "Short content"

        mock_client.get_filing_by_accession.return_value = mock_filing

        result = get_filing_document("MSFT", "0001564590-23-012345")

        assert result["success"] is True
        assert result["truncated"] is False

    @patch("src.tools.fetch.get_edgar_client")
    def test_get_filing_document_not_found(self, mock_get_client: Mock) -> None:
        """Test handling filing not found."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_filing_by_accession.return_value = None

        result = get_filing_document("INVALID", "0000000000-00-000000")

        assert result["success"] is False
        assert "not found" in result["error"]

    @patch("src.tools.fetch.get_edgar_client")
    def test_get_filing_document_no_text_method(self, mock_get_client: Mock) -> None:
        """Test handling filing object without text() method."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock filing without text() method
        mock_filing = MagicMock()
        mock_filing.form = "8-K"
        mock_filing.filing_date = date(2023, 11, 1)
        del mock_filing.text  # Remove text method

        mock_client.get_filing_by_accession.return_value = mock_filing

        result = get_filing_document("TEST", "0001234567-23-000001")

        # Should fallback to str(filing)
        assert result["success"] is True
        assert result["form_type"] == "8-K"

    @patch("src.tools.fetch.get_edgar_client")
    def test_get_filing_document_error(self, mock_get_client: Mock) -> None:
        """Test handling errors during document fetch."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_filing = MagicMock()
        mock_filing.form = "10-K"
        mock_filing.filing_date = date(2023, 10, 27)
        mock_filing.text.side_effect = Exception("Network error")

        mock_client.get_filing_by_accession.return_value = mock_filing

        result = get_filing_document("TEST", "0001234567-23-000001")

        assert result["success"] is False
        assert "Network error" in result["error"]


class TestGetFilingSection:
    """Tests for get_filing_section function."""

    @patch("src.tools.fetch.get_edgar_client")
    def test_get_filing_section_success(self, mock_get_client: Mock) -> None:
        """Test successfully extracting a section."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock filing object
        mock_filing = MagicMock()
        mock_filing.form = "10-K"
        mock_filing.filing_date = date(2023, 10, 27)

        # Mock the TenK object with section content
        mock_tenk = MagicMock()
        mock_tenk.item_1a = "Risk factors content: We face various operational risks..."
        mock_filing.obj.return_value = mock_tenk

        mock_client.get_filing_by_accession.return_value = mock_filing

        result = get_filing_section("AAPL", "0000320193-23-000106", "Risk Factors")

        assert result["success"] is True
        assert result["ticker"] == "AAPL"
        assert result["section"] == "Risk Factors"
        assert result["item"] == "Item 1A"
        assert "Risk factors content" in result["content"]
        assert "citations" in result

    @patch("src.tools.fetch.get_edgar_client")
    def test_get_filing_section_mda(self, mock_get_client: Mock) -> None:
        """Test extracting MD&A section."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_filing = MagicMock()
        mock_filing.form = "10-K"
        mock_filing.filing_date = date(2023, 10, 27)

        mock_tenk = MagicMock()
        mock_tenk.item_7 = "Management's Discussion and Analysis content..."
        mock_filing.obj.return_value = mock_tenk

        mock_client.get_filing_by_accession.return_value = mock_filing

        result = get_filing_section("MSFT", "0001564590-23-012345", "MD&A")

        assert result["success"] is True
        assert result["section"] == "MD&A"
        assert result["item"] == "Item 7"
        assert "Management's Discussion" in result["content"]

    @patch("src.tools.fetch.get_edgar_client")
    def test_get_filing_section_truncation(self, mock_get_client: Mock) -> None:
        """Test section content truncation for large sections."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_filing = MagicMock()
        mock_filing.form = "10-K"
        mock_filing.filing_date = date(2023, 10, 27)

        # Large section content
        large_content = "X" * 50000
        mock_tenk = MagicMock()
        mock_tenk.item_1 = large_content
        mock_filing.obj.return_value = mock_tenk

        mock_client.get_filing_by_accession.return_value = mock_filing

        result = get_filing_section("TEST", "0001234567-23-000001", "Business")

        assert result["success"] is True
        assert len(result["content"]) <= 30025  # 30000 + truncation message (with margin)
        assert "[... truncated ...]" in result["content"]

    @patch("src.tools.fetch.get_edgar_client")
    def test_get_filing_section_fallback_to_text_search(self, mock_get_client: Mock) -> None:
        """Test fallback to text search when section accessor not available."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_filing = MagicMock()
        mock_filing.form = "10-K"
        mock_filing.filing_date = date(2023, 10, 27)

        # Mock obj without section attributes
        mock_tenk = MagicMock(spec=[])  # Empty spec, no attributes
        mock_filing.obj.return_value = mock_tenk

        # Provide text content with section markers
        filing_text = """
        ITEM 1. BUSINESS
        Our business description goes here...
        ITEM 1A. RISK FACTORS
        Risk factors content...
        """
        mock_filing.text.return_value = filing_text

        mock_client.get_filing_by_accession.return_value = mock_filing

        result = get_filing_section("TEST", "0001234567-23-000001", "Business")

        assert result["success"] is True
        assert "business description" in result["content"].lower()

    @patch("src.tools.fetch.get_edgar_client")
    def test_get_filing_section_not_found(self, mock_get_client: Mock) -> None:
        """Test handling section not found in filing."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_filing = MagicMock()
        mock_filing.form = "10-K"
        mock_filing.filing_date = date(2023, 10, 27)

        # Mock obj without the requested section
        mock_tenk = MagicMock(spec=[])
        mock_filing.obj.return_value = mock_tenk

        # Text without the requested section
        mock_filing.text.return_value = "Some other content without the section"

        mock_client.get_filing_by_accession.return_value = mock_filing

        result = get_filing_section("TEST", "0001234567-23-000001", "Risk Factors")

        assert result["success"] is False
        assert "not found" in result["error"]

    @patch("src.tools.fetch.get_edgar_client")
    def test_get_filing_section_filing_not_found(self, mock_get_client: Mock) -> None:
        """Test handling filing not found."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_filing_by_accession.return_value = None

        result = get_filing_section("INVALID", "0000000000-00-000000", "Business")

        assert result["success"] is False
        assert "not found" in result["error"]

    @patch("src.tools.fetch.get_edgar_client")
    def test_get_filing_section_error(self, mock_get_client: Mock) -> None:
        """Test handling errors during section extraction."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_filing = MagicMock()
        mock_filing.obj.side_effect = Exception("Parse error")

        mock_client.get_filing_by_accession.return_value = mock_filing

        result = get_filing_section("TEST", "0001234567-23-000001", "Business")

        assert result["success"] is False
        assert "Parse error" in result["error"]


class TestGetFilingExhibits:
    """Tests for get_filing_exhibits function."""

    @patch("src.tools.fetch.get_edgar_client")
    def test_get_filing_exhibits_success(self, mock_get_client: Mock) -> None:
        """Test successfully retrieving filing exhibits."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock filing with exhibits
        mock_exhibit1 = MagicMock()
        mock_exhibit1.number = "10.1"
        mock_exhibit1.description = "Employment Agreement"
        mock_exhibit1.url = "https://www.sec.gov/Archives/edgar/data/320193/000032019323000106/ex101.htm"

        mock_exhibit2 = MagicMock()
        mock_exhibit2.number = "31.1"
        mock_exhibit2.description = "CEO Certification"
        mock_exhibit2.url = "https://www.sec.gov/Archives/edgar/data/320193/000032019323000106/ex311.htm"

        mock_filing = MagicMock()
        mock_filing.exhibits = [mock_exhibit1, mock_exhibit2]

        mock_client.get_filing_by_accession.return_value = mock_filing

        result = get_filing_exhibits("AAPL", "0000320193-23-000106")

        assert result["success"] is True
        assert result["ticker"] == "AAPL"
        assert result["accession_number"] == "0000320193-23-000106"
        assert result["exhibit_count"] == 2
        assert len(result["exhibits"]) == 2

        # Check first exhibit
        assert result["exhibits"][0]["number"] == "10.1"
        assert result["exhibits"][0]["description"] == "Employment Agreement"
        assert "sec.gov" in result["exhibits"][0]["url"]

    @patch("src.tools.fetch.get_edgar_client")
    def test_get_filing_exhibits_no_exhibits(self, mock_get_client: Mock) -> None:
        """Test handling filing with no exhibits."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_filing = MagicMock()
        mock_filing.exhibits = []

        mock_client.get_filing_by_accession.return_value = mock_filing

        result = get_filing_exhibits("TEST", "0001234567-23-000001")

        assert result["success"] is True
        assert result["exhibit_count"] == 0
        assert result["exhibits"] == []

    @patch("src.tools.fetch.get_edgar_client")
    def test_get_filing_exhibits_no_exhibits_attribute(self, mock_get_client: Mock) -> None:
        """Test handling filing object without exhibits attribute."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock filing without exhibits attribute
        mock_filing = MagicMock(spec=[])  # Empty spec, no attributes

        mock_client.get_filing_by_accession.return_value = mock_filing

        result = get_filing_exhibits("TEST", "0001234567-23-000001")

        assert result["success"] is True
        assert result["exhibit_count"] == 0
        assert result["exhibits"] == []

    @patch("src.tools.fetch.get_edgar_client")
    def test_get_filing_exhibits_filing_not_found(self, mock_get_client: Mock) -> None:
        """Test handling filing not found."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_filing_by_accession.return_value = None

        result = get_filing_exhibits("INVALID", "0000000000-00-000000")

        assert result["success"] is False
        assert "not found" in result["error"]

    @patch("src.tools.fetch.get_edgar_client")
    def test_get_filing_exhibits_error(self, mock_get_client: Mock) -> None:
        """Test handling errors during exhibit retrieval."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_filing = MagicMock()
        # Make exhibits property raise an exception
        type(mock_filing).exhibits = property(lambda self: (_ for _ in ()).throw(Exception("API error")))

        mock_client.get_filing_by_accession.return_value = mock_filing

        result = get_filing_exhibits("TEST", "0001234567-23-000001")

        assert result["success"] is False
        assert "error" in result


class TestFetchToolsIntegration:
    """Integration tests that hit real SEC API (mark as slow)."""

    @pytest.mark.slow
    def test_get_filing_document_integration(self) -> None:
        """Test fetching real filing document."""
        # Use a known recent Apple 10-K
        result = get_filing_document("AAPL", "0000320193-23-000106", max_length=10000)

        assert result["success"] is True
        assert result["ticker"] == "AAPL"
        assert result["form_type"] == "10-K"
        assert len(result["content"]) > 0

    @pytest.mark.slow
    def test_get_filing_section_integration(self) -> None:
        """Test extracting real filing section."""
        result = get_filing_section("AAPL", "0000320193-23-000106", "Risk Factors")

        assert result["success"] is True
        assert result["section"] == "Risk Factors"
        assert len(result["content"]) > 0

    @pytest.mark.slow
    def test_get_filing_exhibits_integration(self) -> None:
        """Test listing real filing exhibits."""
        result = get_filing_exhibits("AAPL", "0000320193-23-000106")

        assert result["success"] is True
        assert result["exhibit_count"] >= 0
        assert isinstance(result["exhibits"], list)
