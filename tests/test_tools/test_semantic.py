"""Tests for semantic search tools."""

from datetime import date
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.data.models import Company, Filing
from src.tools import registry
from src.tools.semantic import (
    find_similar_disclosures,
    index_filing,
    semantic_search,
)


class TestSemanticToolsRegistry:
    """Tests for semantic tool registration."""

    def test_tools_registered(self) -> None:
        """Verify semantic tools are registered."""
        tools = registry.list_tools()
        assert "index_filing" in tools
        assert "semantic_search" in tools
        assert "find_similar_disclosures" in tools


class TestIndexFiling:
    """Tests for index_filing function."""

    @patch("src.tools.semantic.get_vector_store")
    @patch("src.tools.semantic.get_edgar_client")
    def test_index_filing_success(
        self, mock_get_client: Mock, mock_get_vector_store: Mock
    ) -> None:
        """Test successfully indexing a filing."""
        # Mock EDGAR client
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

        # Mock filing object with sections
        mock_edgar_filing = MagicMock()
        mock_tenk = MagicMock()
        mock_tenk.item_1a = "Risk factors content: " + "A" * 200
        mock_tenk.item_7 = "MD&A content: " + "B" * 200
        mock_edgar_filing.obj.return_value = mock_tenk
        mock_client.get_filing_by_accession.return_value = mock_edgar_filing

        # Mock vector store
        mock_vector_store = MagicMock()
        mock_get_vector_store.return_value = mock_vector_store

        result = index_filing("AAPL", form_type="10-K")

        assert result["success"] is True
        assert result["ticker"] == "AAPL"
        assert result["filing"]["form_type"] == "10-K"
        assert result["filing"]["accession_number"] == "0000320193-23-000106"
        assert len(result["indexed_sections"]) == 2

        # Verify vector store was called for each section
        assert mock_vector_store.add_filing_section.call_count == 2

    @patch("src.tools.semantic.get_vector_store")
    @patch("src.tools.semantic.get_edgar_client")
    def test_index_filing_custom_sections(
        self, mock_get_client: Mock, mock_get_vector_store: Mock
    ) -> None:
        """Test indexing custom sections."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        company = Company(
            cik="123", ticker="TEST", name="Test", sic=None, sic_description=None, exchange=None
        )
        filing = Filing(
            accession_number="123",
            form_type="10-K",
            filing_date=date(2023, 1, 1),
            report_date=None,
            company=company,
            primary_document="test.htm",
            url="https://www.sec.gov/test",
        )

        mock_client.get_filings.return_value = [filing]

        mock_edgar_filing = MagicMock()
        mock_tenk = MagicMock()
        mock_tenk.item_1 = "Business section content: " + "C" * 200
        mock_edgar_filing.obj.return_value = mock_tenk
        mock_client.get_filing_by_accession.return_value = mock_edgar_filing

        mock_vector_store = MagicMock()
        mock_get_vector_store.return_value = mock_vector_store

        result = index_filing("TEST", sections=["Business"])

        assert result["success"] is True
        assert len(result["indexed_sections"]) == 1
        assert result["indexed_sections"][0]["section"] == "Business"

    @patch("src.tools.semantic.get_vector_store")
    @patch("src.tools.semantic.get_edgar_client")
    def test_index_filing_no_filings_found(
        self, mock_get_client: Mock, mock_get_vector_store: Mock
    ) -> None:
        """Test when no filings are found."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_filings.return_value = []

        result = index_filing("INVALID")

        assert result["success"] is False
        assert "No 10-K filings found" in result["error"]

    @patch("src.tools.semantic.get_vector_store")
    @patch("src.tools.semantic.get_edgar_client")
    def test_index_filing_cannot_fetch_content(
        self, mock_get_client: Mock, mock_get_vector_store: Mock
    ) -> None:
        """Test when filing content cannot be fetched."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        company = Company(
            cik="123", ticker="TEST", name="Test", sic=None, sic_description=None, exchange=None
        )
        filing = Filing(
            accession_number="123",
            form_type="10-K",
            filing_date=date(2023, 1, 1),
            report_date=None,
            company=company,
            primary_document="test.htm",
            url="https://www.sec.gov/test",
        )

        mock_client.get_filings.return_value = [filing]
        mock_client.get_filing_by_accession.return_value = None

        result = index_filing("TEST")

        assert result["success"] is False
        assert "Could not fetch filing content" in result["error"]

    @patch("src.tools.semantic.get_vector_store")
    @patch("src.tools.semantic.get_edgar_client")
    def test_index_filing_skips_short_content(
        self, mock_get_client: Mock, mock_get_vector_store: Mock
    ) -> None:
        """Test that short content (<100 chars) is skipped."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        company = Company(
            cik="123", ticker="TEST", name="Test", sic=None, sic_description=None, exchange=None
        )
        filing = Filing(
            accession_number="123",
            form_type="10-K",
            filing_date=date(2023, 1, 1),
            report_date=None,
            company=company,
            primary_document="test.htm",
            url="https://www.sec.gov/test",
        )

        mock_client.get_filings.return_value = [filing]

        mock_edgar_filing = MagicMock()
        mock_tenk = MagicMock()
        mock_tenk.item_1a = "Short"  # Less than 100 chars
        mock_edgar_filing.obj.return_value = mock_tenk
        mock_client.get_filing_by_accession.return_value = mock_edgar_filing

        mock_vector_store = MagicMock()
        mock_get_vector_store.return_value = mock_vector_store

        result = index_filing("TEST")

        assert result["success"] is True
        assert len(result["indexed_sections"]) == 0
        mock_vector_store.add_filing_section.assert_not_called()

    @patch("src.tools.semantic.get_vector_store")
    @patch("src.tools.semantic.get_edgar_client")
    def test_index_filing_handles_section_errors(
        self, mock_get_client: Mock, mock_get_vector_store: Mock
    ) -> None:
        """Test that section indexing errors are caught and logged."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        company = Company(
            cik="123", ticker="TEST", name="Test", sic=None, sic_description=None, exchange=None
        )
        filing = Filing(
            accession_number="123",
            form_type="10-K",
            filing_date=date(2023, 1, 1),
            report_date=None,
            company=company,
            primary_document="test.htm",
            url="https://www.sec.gov/test",
        )

        mock_client.get_filings.return_value = [filing]

        mock_edgar_filing = MagicMock()
        MagicMock()
        # Make obj() raise an error
        mock_edgar_filing.obj.side_effect = Exception("Parse error")
        mock_client.get_filing_by_accession.return_value = mock_edgar_filing

        mock_vector_store = MagicMock()
        mock_get_vector_store.return_value = mock_vector_store

        # Should not raise exception, but return success with no indexed sections
        result = index_filing("TEST")

        assert result["success"] is True
        assert len(result["indexed_sections"]) == 0


class TestSemanticSearch:
    """Tests for semantic_search function."""

    @patch("src.tools.semantic.get_vector_store")
    def test_semantic_search_with_results(self, mock_get_vector_store: Mock) -> None:
        """Test semantic search returning results."""
        mock_vector_store = MagicMock()
        mock_get_vector_store.return_value = mock_vector_store

        mock_vector_store.search.return_value = [
            {
                "content": "Risk factors content from AAPL filing...",
                "metadata": {
                    "ticker": "AAPL",
                    "section_name": "Risk Factors",
                    "filing_date": "2023-10-27",
                },
                "distance": 0.2,
            },
            {
                "content": "More risk content from MSFT...",
                "metadata": {
                    "ticker": "MSFT",
                    "section_name": "Risk Factors",
                    "filing_date": "2023-07-28",
                },
                "distance": 0.3,
            },
        ]

        result = semantic_search("What are the main risks?", limit=5)

        assert result["success"] is True
        assert result["query"] == "What are the main risks?"
        assert result["result_count"] == 2
        assert len(result["results"]) == 2

        # Check first result
        assert result["results"][0]["ticker"] == "AAPL"
        assert result["results"][0]["section"] == "Risk Factors"
        assert result["results"][0]["relevance_score"] == 0.8  # 1 - 0.2

        # Verify search was called correctly
        mock_vector_store.search.assert_called_once_with(
            query="What are the main risks?",
            ticker=None,
            limit=5,
        )

    @patch("src.tools.semantic.get_vector_store")
    def test_semantic_search_with_ticker_filter(self, mock_get_vector_store: Mock) -> None:
        """Test semantic search filtered by ticker."""
        mock_vector_store = MagicMock()
        mock_get_vector_store.return_value = mock_vector_store

        mock_vector_store.search.return_value = [
            {
                "content": "Content",
                "metadata": {"ticker": "AAPL", "section_name": "Risk Factors", "filing_date": "2023-10-27"},
                "distance": 0.1,
            }
        ]

        result = semantic_search("query", ticker="AAPL", limit=3)

        assert result["success"] is True
        mock_vector_store.search.assert_called_once_with(
            query="query",
            ticker="AAPL",
            limit=3,
        )

    @patch("src.tools.semantic.get_vector_store")
    def test_semantic_search_no_results(self, mock_get_vector_store: Mock) -> None:
        """Test semantic search with no results."""
        mock_vector_store = MagicMock()
        mock_get_vector_store.return_value = mock_vector_store
        mock_vector_store.search.return_value = []

        result = semantic_search("unknown query")

        assert result["success"] is True
        assert "No matching content found" in result["message"]
        assert result["results"] == []

    @patch("src.tools.semantic.get_vector_store")
    def test_semantic_search_truncates_long_content(self, mock_get_vector_store: Mock) -> None:
        """Test that long content is truncated in results."""
        mock_vector_store = MagicMock()
        mock_get_vector_store.return_value = mock_vector_store

        long_content = "A" * 1000
        mock_vector_store.search.return_value = [
            {
                "content": long_content,
                "metadata": {"ticker": "TEST", "section_name": "Test", "filing_date": "2023-01-01"},
                "distance": 0.1,
            }
        ]

        result = semantic_search("query")

        # Should be truncated to 500 chars + "..."
        assert len(result["results"][0]["excerpt"]) == 503
        assert result["results"][0]["excerpt"].endswith("...")

    @patch("src.tools.semantic.get_vector_store")
    def test_semantic_search_error_handling(self, mock_get_vector_store: Mock) -> None:
        """Test error handling in semantic search."""
        mock_vector_store = MagicMock()
        mock_get_vector_store.return_value = mock_vector_store
        mock_vector_store.search.side_effect = Exception("Database error")

        result = semantic_search("query")

        assert result["success"] is False
        assert "Database error" in result["error"]


class TestFindSimilarDisclosures:
    """Tests for find_similar_disclosures function."""

    @patch("src.tools.semantic.get_vector_store")
    @patch("src.tools.semantic.get_edgar_client")
    def test_find_similar_disclosures_success(
        self, mock_get_client: Mock, mock_get_vector_store: Mock
    ) -> None:
        """Test successfully finding similar disclosures."""
        # Mock EDGAR client
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

        # Mock filing object
        mock_edgar_filing = MagicMock()
        mock_tenk = MagicMock()
        mock_tenk.item_1a = "Risk factors content from AAPL: " + "A" * 200
        mock_edgar_filing.obj.return_value = mock_tenk
        mock_client.get_filing_by_accession.return_value = mock_edgar_filing

        # Mock vector store
        mock_vector_store = MagicMock()
        mock_get_vector_store.return_value = mock_vector_store

        mock_vector_store.search_similar.return_value = [
            {
                "content": "Similar risk content from MSFT...",
                "metadata": {"ticker": "MSFT", "section_name": "Risk Factors"},
                "distance": 0.15,
            },
            {
                "content": "Similar risk content from GOOGL...",
                "metadata": {"ticker": "GOOGL", "section_name": "Risk Factors"},
                "distance": 0.25,
            },
        ]

        result = find_similar_disclosures("AAPL", section="Risk Factors", limit=3)

        assert result["success"] is True
        assert result["source"]["ticker"] == "AAPL"
        assert result["source"]["section"] == "Risk Factors"
        assert len(result["similar_companies"]) == 2

        # Check similarity scores
        assert result["similar_companies"][0]["ticker"] == "MSFT"
        assert result["similar_companies"][0]["similarity_score"] == 0.85  # 1 - 0.15

        # Verify vector store was called correctly
        mock_vector_store.search_similar.assert_called_once()

    @patch("src.tools.semantic.get_vector_store")
    @patch("src.tools.semantic.get_edgar_client")
    def test_find_similar_disclosures_no_filings(
        self, mock_get_client: Mock, mock_get_vector_store: Mock
    ) -> None:
        """Test when no filings are found."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_filings.return_value = []

        result = find_similar_disclosures("INVALID")

        assert result["success"] is False
        assert "No 10-K filings found" in result["error"]

    @patch("src.tools.semantic.get_vector_store")
    @patch("src.tools.semantic.get_edgar_client")
    def test_find_similar_disclosures_cannot_extract_section(
        self, mock_get_client: Mock, mock_get_vector_store: Mock
    ) -> None:
        """Test when section cannot be extracted."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        company = Company(
            cik="123", ticker="TEST", name="Test", sic=None, sic_description=None, exchange=None
        )
        filing = Filing(
            accession_number="123",
            form_type="10-K",
            filing_date=date(2023, 1, 1),
            report_date=None,
            company=company,
            primary_document="test.htm",
            url="https://www.sec.gov/test",
        )

        mock_client.get_filings.return_value = [filing]

        mock_edgar_filing = MagicMock()
        mock_tenk = MagicMock(spec=[])  # No attributes
        mock_edgar_filing.obj.return_value = mock_tenk
        mock_client.get_filing_by_accession.return_value = mock_edgar_filing

        result = find_similar_disclosures("TEST")

        assert result["success"] is False
        assert "Could not extract" in result["error"]

    @patch("src.tools.semantic.get_vector_store")
    @patch("src.tools.semantic.get_edgar_client")
    def test_find_similar_disclosures_error_handling(
        self, mock_get_client: Mock, mock_get_vector_store: Mock
    ) -> None:
        """Test error handling in similar disclosures."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_filings.side_effect = Exception("API error")

        result = find_similar_disclosures("AAPL")

        assert result["success"] is False
        assert "API error" in result["error"]


class TestSemanticToolsIntegration:
    """Integration tests (mark as slow)."""

    @pytest.mark.slow
    def test_index_and_search_integration(self) -> None:
        """Test indexing and searching a real filing."""
        # This would test against real SEC API and ChromaDB
        # Skip for now as it requires actual infrastructure
        pass
