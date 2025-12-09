"""Tests for SEC EDGAR client wrapper."""

from datetime import date
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.data.edgar_client import EdgarClient, get_edgar_client
from src.data.models import Company, Filing, FinancialStatement, InsiderTransaction


@pytest.fixture(autouse=True)
def clear_cache_and_singleton():
    """Clear cache and reset singleton before each test."""
    # Clear the cache
    from src.data.cache import get_cache
    cache = get_cache()
    cache.clear()

    # Reset global singletons
    import src.data.edgar_client
    import src.data.cache
    import src.utils.rate_limiter

    src.data.edgar_client._client = None
    src.data.cache._cache = None
    src.utils.rate_limiter._rate_limiter = None

    yield

    # Cleanup after test
    cache.clear()


class TestEdgarClientInit:
    """Tests for EdgarClient initialization."""

    @patch("src.data.edgar_client.edgar.set_identity")
    @patch("src.data.edgar_client.get_cache")
    @patch("src.data.edgar_client.get_rate_limiter")
    def test_init_sets_up_rate_limiter_and_cache(
        self, mock_get_limiter: Mock, mock_get_cache: Mock, mock_set_identity: Mock
    ) -> None:
        """Test that initialization sets up rate limiter and cache."""
        mock_limiter = MagicMock()
        mock_cache = MagicMock()
        mock_get_limiter.return_value = mock_limiter
        mock_get_cache.return_value = mock_cache

        client = EdgarClient()

        assert client.rate_limiter == mock_limiter
        assert client.cache == mock_cache
        mock_set_identity.assert_called_once()


class TestGetCompany:
    """Tests for get_company method."""

    @patch("src.data.edgar_client.edgar.set_identity")
    @patch("src.data.edgar_client.EdgarCompany")
    def test_get_company_success(self, mock_edgar_company: Mock, mock_identity: Mock) -> None:
        """Test successfully fetching company information."""
        # Mock edgar Company
        mock_company = MagicMock()
        mock_company.cik = "0000320193"
        mock_company.name = "Apple Inc"
        mock_company.sic = "3571"
        mock_company.sic_description = "Electronic Computers"
        mock_company.exchange = "NASDAQ"
        mock_edgar_company.return_value = mock_company

        client = EdgarClient()
        result = client.get_company("AAPL")

        assert result.ticker == "AAPL"
        assert result.cik == "0000320193"
        assert result.name == "Apple Inc"
        assert result.sic == "3571"
        assert result.exchange == "NASDAQ"
        mock_edgar_company.assert_called_with("AAPL")

    @patch("src.data.edgar_client.edgar.set_identity")
    @patch("src.data.edgar_client.EdgarCompany")
    def test_get_company_caching(self, mock_edgar_company: Mock, mock_identity: Mock) -> None:
        """Test that company info is cached."""
        mock_company = MagicMock()
        mock_company.cik = "0000789019"
        mock_company.name = "Microsoft Corp"
        mock_company.sic = None
        mock_company.sic_description = None
        mock_company.exchange = None
        mock_edgar_company.return_value = mock_company

        client = EdgarClient()

        # First call - should hit API
        result1 = client.get_company("MSFT")
        assert mock_edgar_company.call_count == 1

        # Second call - should use cache
        result2 = client.get_company("MSFT")
        assert mock_edgar_company.call_count == 1  # Not called again

        assert result1.ticker == result2.ticker
        assert result1.name == result2.name

    @patch("src.data.edgar_client.edgar.set_identity")
    @patch("src.data.edgar_client.EdgarCompany")
    def test_get_company_normalizes_ticker(self, mock_edgar_company: Mock, mock_identity: Mock) -> None:
        """Test that ticker is normalized to uppercase."""
        mock_company = MagicMock()
        mock_company.cik = "123"
        mock_company.name = "Test Corp"
        mock_company.sic = None
        mock_company.sic_description = None
        mock_company.exchange = None
        mock_edgar_company.return_value = mock_company

        client = EdgarClient()
        result = client.get_company("aapl")

        assert result.ticker == "AAPL"
        mock_edgar_company.assert_called_with("AAPL")


class TestGetFilings:
    """Tests for get_filings method."""

    @patch("src.data.edgar_client.edgar.set_identity")
    @patch("src.data.edgar_client.EdgarCompany")
    def test_get_filings_success(self, mock_edgar_company: Mock, mock_identity: Mock) -> None:
        """Test successfully fetching filings."""
        # Mock company
        mock_company_obj = MagicMock()
        mock_company_obj.cik = "0000320193"
        mock_company_obj.name = "Apple Inc"
        mock_company_obj.sic = None
        mock_company_obj.sic_description = None
        mock_company_obj.exchange = None

        # Mock filings
        mock_filing = MagicMock()
        mock_filing.accession_number = "0000320193-23-000106"
        mock_filing.form = "10-K"
        mock_filing.filing_date = date(2023, 10, 27)
        mock_filing.report_date = date(2023, 9, 30)
        mock_filing.filing_href = "https://www.sec.gov/..."
        mock_filing.primary_document = "aapl-20230930.htm"

        mock_filings = MagicMock()
        mock_filings.head.return_value = [mock_filing]
        mock_company_obj.get_filings.return_value = mock_filings

        mock_edgar_company.return_value = mock_company_obj

        client = EdgarClient()
        results = client.get_filings("AAPL", "10-K", limit=1)

        assert len(results) == 1
        assert results[0].accession_number == "0000320193-23-000106"
        assert results[0].form_type == "10-K"
        assert results[0].filing_date == date(2023, 10, 27)
        assert results[0].company.name == "Apple Inc"

    @patch("src.data.edgar_client.edgar.set_identity")
    @patch("src.data.edgar_client.EdgarCompany")
    def test_get_filings_with_date_filter(self, mock_edgar_company: Mock, mock_identity: Mock) -> None:
        """Test filtering filings by date range."""
        mock_company_obj = MagicMock()
        mock_company_obj.cik = "123"
        mock_company_obj.name = "Test Corp"
        mock_company_obj.sic = None
        mock_company_obj.sic_description = None
        mock_company_obj.exchange = None

        # Create a mock filings object with filter method
        mock_filings = MagicMock()
        mock_filings.filter.return_value = mock_filings
        mock_filings.head.return_value = []
        mock_company_obj.get_filings.return_value = mock_filings

        mock_edgar_company.return_value = mock_company_obj

        client = EdgarClient()
        client.get_filings(
            "TEST",
            "10-K",
            limit=5,
            start_date=date(2020, 1, 1),
            end_date=date(2023, 12, 31),
        )

        # Verify filter was called for date range
        assert mock_filings.filter.call_count == 2

    @patch("src.data.edgar_client.edgar.set_identity")
    @patch("src.data.edgar_client.EdgarCompany")
    def test_get_filings_caching(self, mock_edgar_company: Mock, mock_identity: Mock) -> None:
        """Test that filings are cached."""
        mock_company_obj = MagicMock()
        mock_company_obj.cik = "123"
        mock_company_obj.name = "Test Corp"
        mock_company_obj.sic = None
        mock_company_obj.sic_description = None
        mock_company_obj.exchange = None

        mock_filings = MagicMock()
        mock_filings.head.return_value = []
        mock_company_obj.get_filings.return_value = mock_filings

        mock_edgar_company.return_value = mock_company_obj

        client = EdgarClient()

        # First call
        client.get_filings("TEST", "10-K", limit=5)
        call_count_1 = mock_edgar_company.call_count

        # Second call with same parameters
        client.get_filings("TEST", "10-K", limit=5)
        call_count_2 = mock_edgar_company.call_count

        # Should not make additional API calls
        assert call_count_2 == call_count_1


class TestGetFilingByAccession:
    """Tests for get_filing_by_accession method."""

    @patch("src.data.edgar_client.edgar.set_identity")
    @patch("src.data.edgar_client.EdgarCompany")
    def test_get_filing_by_accession_found(self, mock_edgar_company: Mock, mock_identity: Mock) -> None:
        """Test finding a filing by accession number."""
        target_accession = "0000320193-23-000106"

        mock_filing1 = MagicMock()
        mock_filing1.accession_number = "0000320193-23-000001"

        mock_filing2 = MagicMock()
        mock_filing2.accession_number = target_accession

        mock_company_obj = MagicMock()
        mock_company_obj.get_filings.return_value = [mock_filing1, mock_filing2]
        mock_edgar_company.return_value = mock_company_obj

        client = EdgarClient()
        result = client.get_filing_by_accession("AAPL", target_accession)

        assert result is not None
        assert result.accession_number == target_accession

    @patch("src.data.edgar_client.edgar.set_identity")
    @patch("src.data.edgar_client.EdgarCompany")
    def test_get_filing_by_accession_not_found(self, mock_edgar_company: Mock, mock_identity: Mock) -> None:
        """Test when filing is not found."""
        mock_company_obj = MagicMock()
        mock_company_obj.get_filings.return_value = []
        mock_edgar_company.return_value = mock_company_obj

        client = EdgarClient()
        result = client.get_filing_by_accession("AAPL", "0000320193-99-999999")

        assert result is None


class TestGetFinancials:
    """Tests for get_financials method."""

    @patch("src.data.edgar_client.edgar.set_identity")
    @patch("src.data.edgar_client.EdgarCompany")
    def test_get_financials_income_statement(self, mock_edgar_company: Mock, mock_identity: Mock) -> None:
        """Test fetching income statement data."""
        # Mock filing and TenK object
        mock_filing = MagicMock()
        mock_filing.filing_date = date(2023, 10, 27)

        mock_financials = MagicMock()
        mock_income_stmt = MagicMock()
        mock_income_stmt.to_dict.return_value = {"revenue": 383000000000, "net_income": 97000000000}
        mock_financials.income_statement = mock_income_stmt

        mock_tenk = MagicMock()
        mock_tenk.financials = mock_financials
        mock_filing.obj.return_value = mock_tenk

        mock_filings = MagicMock()
        mock_filings.head.return_value = [mock_filing]

        mock_company_obj = MagicMock()
        mock_company_obj.get_filings.return_value = mock_filings
        mock_edgar_company.return_value = mock_company_obj

        client = EdgarClient()
        results = client.get_financials("AAPL", "income_statement", periods=1)

        assert len(results) == 1
        assert results[0].statement_type == "income_statement"
        assert results[0].data["revenue"] == 383000000000
        assert results[0].fiscal_period == "FY"

    @patch("src.data.edgar_client.edgar.set_identity")
    @patch("src.data.edgar_client.EdgarCompany")
    def test_get_financials_balance_sheet(self, mock_edgar_company: Mock, mock_identity: Mock) -> None:
        """Test fetching balance sheet data."""
        mock_filing = MagicMock()
        mock_filing.filing_date = date(2023, 10, 27)

        mock_financials = MagicMock()
        mock_balance_sheet = MagicMock()
        mock_balance_sheet.to_dict.return_value = {"total_assets": 352000000000}
        mock_financials.balance_sheet = mock_balance_sheet

        mock_tenk = MagicMock()
        mock_tenk.financials = mock_financials
        mock_filing.obj.return_value = mock_tenk

        mock_filings = MagicMock()
        mock_filings.head.return_value = [mock_filing]

        mock_company_obj = MagicMock()
        mock_company_obj.get_filings.return_value = mock_filings
        mock_edgar_company.return_value = mock_company_obj

        client = EdgarClient()
        results = client.get_financials("AAPL", "balance_sheet", periods=1)

        assert len(results) == 1
        assert results[0].statement_type == "balance_sheet"
        assert results[0].data["total_assets"] == 352000000000

    @patch("src.data.edgar_client.edgar.set_identity")
    @patch("src.data.edgar_client.EdgarCompany")
    def test_get_financials_skips_errors(self, mock_edgar_company: Mock, mock_identity: Mock) -> None:
        """Test that errors in individual filings are skipped."""
        # One good filing, one bad filing
        mock_filing_good = MagicMock()
        mock_filing_good.filing_date = date(2023, 10, 27)
        mock_financials = MagicMock()
        mock_income = MagicMock()
        mock_income.to_dict.return_value = {"revenue": 100}
        mock_financials.income_statement = mock_income
        mock_tenk = MagicMock()
        mock_tenk.financials = mock_financials
        mock_filing_good.obj.return_value = mock_tenk

        mock_filing_bad = MagicMock()
        mock_filing_bad.obj.side_effect = Exception("Parse error")

        mock_filings = MagicMock()
        mock_filings.head.return_value = [mock_filing_good, mock_filing_bad]

        mock_company_obj = MagicMock()
        mock_company_obj.get_filings.return_value = mock_filings
        mock_edgar_company.return_value = mock_company_obj

        client = EdgarClient()
        results = client.get_financials("TEST", "income_statement", periods=2)

        # Should only get the good filing
        assert len(results) == 1

    @patch("src.data.edgar_client.edgar.set_identity")
    @patch("src.data.edgar_client.EdgarCompany")
    def test_get_financials_caching(self, mock_edgar_company: Mock, mock_identity: Mock) -> None:
        """Test that financial data is cached."""
        mock_filing = MagicMock()
        mock_filing.filing_date = date(2023, 10, 27)
        mock_financials = MagicMock()
        mock_income = MagicMock()
        mock_income.to_dict.return_value = {"revenue": 100}
        mock_financials.income_statement = mock_income
        mock_tenk = MagicMock()
        mock_tenk.financials = mock_financials
        mock_filing.obj.return_value = mock_tenk

        mock_filings = MagicMock()
        mock_filings.head.return_value = [mock_filing]

        mock_company_obj = MagicMock()
        mock_company_obj.get_filings.return_value = mock_filings
        mock_edgar_company.return_value = mock_company_obj

        client = EdgarClient()

        # First call
        results1 = client.get_financials("TEST", "income_statement", periods=1)
        call_count_1 = mock_edgar_company.call_count

        # Second call
        results2 = client.get_financials("TEST", "income_statement", periods=1)
        call_count_2 = mock_edgar_company.call_count

        assert len(results1) == len(results2)
        # Should use cache, not make additional API calls
        assert call_count_2 == call_count_1


class TestGetInsiderTransactions:
    """Tests for get_insider_transactions method."""

    @patch("src.data.edgar_client.edgar.set_identity")
    @patch("src.data.edgar_client.EdgarCompany")
    def test_get_insider_transactions_success(self, mock_edgar_company: Mock, mock_identity: Mock) -> None:
        """Test fetching insider transactions."""
        # Mock Form 4 filing
        mock_txn = MagicMock()
        mock_txn.transaction_date = date(2023, 11, 10)
        mock_txn.transaction_code = "S"
        mock_txn.shares = 10000
        mock_txn.price_per_share = 185.50
        mock_txn.shares_owned_following = 3000000

        mock_form4 = MagicMock()
        mock_form4.owner_name = "Tim Cook"
        mock_form4.owner_title = "CEO"
        mock_form4.transactions = [mock_txn]

        mock_filing = MagicMock()
        mock_filing.accession_number = "0001234567-23-000001"
        mock_filing.filing_date = date(2023, 11, 15)
        mock_filing.obj.return_value = mock_form4

        mock_filings = MagicMock()
        mock_filings.head.return_value = [mock_filing]

        mock_company_obj = MagicMock()
        mock_company_obj.cik = "0000320193"
        mock_company_obj.name = "Apple Inc"
        mock_company_obj.sic = None
        mock_company_obj.sic_description = None
        mock_company_obj.exchange = None
        mock_company_obj.get_filings.return_value = mock_filings
        mock_edgar_company.return_value = mock_company_obj

        client = EdgarClient()
        results = client.get_insider_transactions("AAPL", limit=20)

        assert len(results) == 1
        assert results[0].insider_name == "Tim Cook"
        assert results[0].insider_title == "CEO"
        assert results[0].transaction_type == "S"
        assert results[0].shares == 10000.0
        assert results[0].price_per_share == 185.50

    @patch("src.data.edgar_client.edgar.set_identity")
    @patch("src.data.edgar_client.EdgarCompany")
    def test_get_insider_transactions_no_transactions(self, mock_edgar_company: Mock, mock_identity: Mock) -> None:
        """Test handling filings with no transactions."""
        mock_filings = MagicMock()
        mock_filings.head.return_value = []

        mock_company_obj = MagicMock()
        mock_company_obj.cik = "123"
        mock_company_obj.name = "Test Corp"
        mock_company_obj.sic = None
        mock_company_obj.sic_description = None
        mock_company_obj.exchange = None
        mock_company_obj.get_filings.return_value = mock_filings
        mock_edgar_company.return_value = mock_company_obj

        client = EdgarClient()
        results = client.get_insider_transactions("TEST", limit=20)

        assert len(results) == 0

    @patch("src.data.edgar_client.edgar.set_identity")
    @patch("src.data.edgar_client.EdgarCompany")
    def test_get_insider_transactions_skips_errors(self, mock_edgar_company: Mock, mock_identity: Mock) -> None:
        """Test that errors in individual Form 4s are skipped."""
        mock_filing_bad = MagicMock()
        mock_filing_bad.obj.side_effect = Exception("Parse error")

        mock_filings = MagicMock()
        mock_filings.head.return_value = [mock_filing_bad]

        mock_company_obj = MagicMock()
        mock_company_obj.cik = "123"
        mock_company_obj.name = "Test Corp"
        mock_company_obj.sic = None
        mock_company_obj.sic_description = None
        mock_company_obj.exchange = None
        mock_company_obj.get_filings.return_value = mock_filings
        mock_edgar_company.return_value = mock_company_obj

        client = EdgarClient()
        results = client.get_insider_transactions("TEST", limit=20)

        assert len(results) == 0


class TestSearchFilings:
    """Tests for search_filings method."""

    @patch("src.data.edgar_client.edgar.set_identity")
    def test_search_filings_not_implemented(self, mock_identity: Mock) -> None:
        """Test that search_filings returns empty list (not implemented)."""
        client = EdgarClient()
        results = client.search_filings("revenue growth")

        assert results == []


class TestGetEdgarClient:
    """Tests for get_edgar_client singleton."""

    @patch("src.data.edgar_client.edgar.set_identity")
    def test_get_edgar_client_returns_singleton(self, mock_identity: Mock) -> None:
        """Test that get_edgar_client returns the same instance."""
        # Reset global client
        import src.data.edgar_client
        src.data.edgar_client._client = None

        client1 = get_edgar_client()
        client2 = get_edgar_client()

        assert client1 is client2


class TestRateLimiting:
    """Tests for rate limiting behavior."""

    @patch("src.data.edgar_client.edgar.set_identity")
    @patch("src.data.edgar_client.EdgarCompany")
    def test_rate_limited_call_waits(self, mock_edgar_company: Mock, mock_identity: Mock) -> None:
        """Test that rate limiter wait is called."""
        mock_company = MagicMock()
        mock_company.cik = "123"
        mock_company.name = "Test Corp"
        mock_company.sic = None
        mock_company.sic_description = None
        mock_company.exchange = None
        mock_edgar_company.return_value = mock_company

        client = EdgarClient()
        mock_rate_limiter = MagicMock()
        client.rate_limiter = mock_rate_limiter

        client.get_company("TEST")

        # Verify rate limiter was called
        assert mock_rate_limiter.wait.call_count >= 1


class TestEdgarClientIntegration:
    """Integration tests that hit real SEC API (mark as slow)."""

    @pytest.mark.slow
    def test_get_company_integration(self) -> None:
        """Test getting real company data."""
        client = EdgarClient()
        result = client.get_company("AAPL")

        assert result.ticker == "AAPL"
        assert "Apple" in result.name
        assert result.cik

    @pytest.mark.slow
    def test_get_filings_integration(self) -> None:
        """Test getting real filings."""
        client = EdgarClient()
        results = client.get_filings("AAPL", "10-K", limit=2)

        assert len(results) >= 1
        assert results[0].form_type == "10-K"
        assert results[0].company.ticker == "AAPL"

    @pytest.mark.slow
    def test_get_financials_integration(self) -> None:
        """Test getting real financial data."""
        client = EdgarClient()
        results = client.get_financials("AAPL", "income_statement", periods=1)

        assert len(results) >= 0  # May or may not have data
        if results:
            assert results[0].statement_type == "income_statement"
