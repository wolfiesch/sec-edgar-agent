"""Tests for watchlist management tools."""

import json
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.data.models import Company, Filing, InsiderTransaction
from src.tools import registry
from src.tools.watchlist import (
    _load_watchlist,
    _save_watchlist,
    add_to_watchlist,
    check_watchlist_updates,
    generate_watchlist_summary,
    get_watchlist,
    remove_from_watchlist,
)


class TestWatchlistToolsRegistry:
    """Tests for watchlist tool registration."""

    def test_tools_registered(self) -> None:
        """Verify watchlist tools are registered."""
        tools = registry.list_tools()
        assert "add_to_watchlist" in tools
        assert "remove_from_watchlist" in tools
        assert "get_watchlist" in tools
        assert "check_watchlist_updates" in tools
        assert "generate_watchlist_summary" in tools


class TestWatchlistHelpers:
    """Tests for watchlist helper functions."""

    def test_load_watchlist_file_exists(self, tmp_path: Path) -> None:
        """Test loading watchlist from existing file."""
        watchlist_file = tmp_path / "watchlist.json"
        data = {
            "companies": {"AAPL": {"name": "Apple Inc", "cik": "123"}},
            "last_check": "2023-11-01T12:00:00",
        }
        watchlist_file.write_text(json.dumps(data))

        with patch("src.tools.watchlist.WATCHLIST_FILE", watchlist_file):
            result = _load_watchlist()
            assert result["companies"]["AAPL"]["name"] == "Apple Inc"
            assert result["last_check"] == "2023-11-01T12:00:00"

    def test_load_watchlist_file_not_exists(self, tmp_path: Path) -> None:
        """Test loading watchlist when file doesn't exist."""
        watchlist_file = tmp_path / "nonexistent.json"

        with patch("src.tools.watchlist.WATCHLIST_FILE", watchlist_file):
            result = _load_watchlist()
            assert result == {"companies": {}, "last_check": None}

    def test_load_watchlist_corrupted_file(self, tmp_path: Path) -> None:
        """Test loading watchlist with corrupted JSON."""
        watchlist_file = tmp_path / "watchlist.json"
        watchlist_file.write_text("invalid json{")

        with patch("src.tools.watchlist.WATCHLIST_FILE", watchlist_file):
            result = _load_watchlist()
            assert result == {"companies": {}, "last_check": None}

    def test_save_watchlist(self, tmp_path: Path) -> None:
        """Test saving watchlist to file."""
        watchlist_file = tmp_path / "watchlist.json"
        data = {
            "companies": {"MSFT": {"name": "Microsoft", "cik": "456"}},
            "last_check": "2023-11-02T10:00:00",
        }

        with patch("src.tools.watchlist.WATCHLIST_FILE", watchlist_file):
            _save_watchlist(data)
            assert watchlist_file.exists()

            # Verify content
            saved = json.loads(watchlist_file.read_text())
            assert saved["companies"]["MSFT"]["name"] == "Microsoft"


class TestAddToWatchlist:
    """Tests for add_to_watchlist function."""

    @patch("src.tools.watchlist._save_watchlist")
    @patch("src.tools.watchlist._load_watchlist")
    @patch("src.tools.watchlist.get_edgar_client")
    def test_add_to_watchlist_success(
        self,
        mock_get_client: Mock,
        mock_load: Mock,
        mock_save: Mock,
    ) -> None:
        """Test successfully adding company to watchlist."""
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
        mock_client.get_company.return_value = company

        # Mock watchlist
        mock_load.return_value = {"companies": {}, "last_check": None}

        result = add_to_watchlist("AAPL", watch_forms=["10-K", "10-Q"], notes="Testing")

        assert result["success"] is True
        assert "Apple Inc" in result["message"]
        assert result["watching"] == ["10-K", "10-Q"]

        # Verify save was called with correct data
        mock_save.assert_called_once()
        saved_data = mock_save.call_args[0][0]
        assert "AAPL" in saved_data["companies"]
        assert saved_data["companies"]["AAPL"]["name"] == "Apple Inc"
        assert saved_data["companies"]["AAPL"]["notes"] == "Testing"

    @patch("src.tools.watchlist._save_watchlist")
    @patch("src.tools.watchlist._load_watchlist")
    @patch("src.tools.watchlist.get_edgar_client")
    def test_add_to_watchlist_default_forms(
        self,
        mock_get_client: Mock,
        mock_load: Mock,
        mock_save: Mock,
    ) -> None:
        """Test adding company with default watch forms."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        company = Company(
            cik="123", ticker="TEST", name="Test", sic=None, sic_description=None, exchange=None
        )
        mock_client.get_company.return_value = company
        mock_load.return_value = {"companies": {}, "last_check": None}

        result = add_to_watchlist("TEST")

        assert result["success"] is True
        saved_data = mock_save.call_args[0][0]
        assert saved_data["companies"]["TEST"]["watch_forms"] == ["10-K", "10-Q", "8-K", "4"]

    @patch("src.tools.watchlist.get_edgar_client")
    def test_add_to_watchlist_invalid_ticker(self, mock_get_client: Mock) -> None:
        """Test adding invalid ticker."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_company.side_effect = Exception("Company not found")

        result = add_to_watchlist("INVALID")

        assert result["success"] is False
        assert "Company not found" in result["error"]


class TestRemoveFromWatchlist:
    """Tests for remove_from_watchlist function."""

    @patch("src.tools.watchlist._save_watchlist")
    @patch("src.tools.watchlist._load_watchlist")
    def test_remove_from_watchlist_success(
        self, mock_load: Mock, mock_save: Mock
    ) -> None:
        """Test successfully removing company from watchlist."""
        mock_load.return_value = {
            "companies": {
                "AAPL": {"name": "Apple Inc", "cik": "123"},
                "MSFT": {"name": "Microsoft", "cik": "456"},
            },
            "last_check": None,
        }

        result = remove_from_watchlist("AAPL")

        assert result["success"] is True
        assert "Apple Inc" in result["message"]

        # Verify save was called without AAPL
        mock_save.assert_called_once()
        saved_data = mock_save.call_args[0][0]
        assert "AAPL" not in saved_data["companies"]
        assert "MSFT" in saved_data["companies"]

    @patch("src.tools.watchlist._load_watchlist")
    def test_remove_from_watchlist_not_in_list(self, mock_load: Mock) -> None:
        """Test removing company not in watchlist."""
        mock_load.return_value = {
            "companies": {"AAPL": {"name": "Apple Inc"}},
            "last_check": None,
        }

        result = remove_from_watchlist("MSFT")

        assert result["success"] is False
        assert "not in watchlist" in result["error"]

    @patch("src.tools.watchlist._save_watchlist")
    @patch("src.tools.watchlist._load_watchlist")
    def test_remove_from_watchlist_case_insensitive(
        self, mock_load: Mock, mock_save: Mock
    ) -> None:
        """Test that ticker matching is case-insensitive."""
        mock_load.return_value = {
            "companies": {"AAPL": {"name": "Apple Inc"}},
            "last_check": None,
        }

        result = remove_from_watchlist("aapl")  # lowercase

        assert result["success"] is True
        saved_data = mock_save.call_args[0][0]
        assert "AAPL" not in saved_data["companies"]


class TestGetWatchlist:
    """Tests for get_watchlist function."""

    @patch("src.tools.watchlist._load_watchlist")
    def test_get_watchlist_with_companies(self, mock_load: Mock) -> None:
        """Test getting watchlist with companies."""
        mock_load.return_value = {
            "companies": {
                "AAPL": {
                    "name": "Apple Inc",
                    "watch_forms": ["10-K", "10-Q"],
                    "notes": "Tech leader",
                    "added": "2023-11-01T10:00:00",
                },
                "MSFT": {
                    "name": "Microsoft",
                    "watch_forms": ["10-K"],
                    "notes": None,
                    "added": "2023-11-02T11:00:00",
                },
            },
            "last_check": None,
        }

        result = get_watchlist()

        assert result["success"] is True
        assert result["count"] == 2
        assert len(result["companies"]) == 2

        # Check AAPL data
        aapl = next(c for c in result["companies"] if c["ticker"] == "AAPL")
        assert aapl["name"] == "Apple Inc"
        assert aapl["watching"] == ["10-K", "10-Q"]
        assert aapl["notes"] == "Tech leader"

    @patch("src.tools.watchlist._load_watchlist")
    def test_get_watchlist_empty(self, mock_load: Mock) -> None:
        """Test getting empty watchlist."""
        mock_load.return_value = {"companies": {}, "last_check": None}

        result = get_watchlist()

        assert result["success"] is True
        assert result["count"] == 0
        assert result["companies"] == []


class TestCheckWatchlistUpdates:
    """Tests for check_watchlist_updates function."""

    @patch("src.tools.watchlist._save_watchlist")
    @patch("src.tools.watchlist._load_watchlist")
    @patch("src.tools.watchlist.get_edgar_client")
    def test_check_watchlist_updates_with_new_filings(
        self,
        mock_get_client: Mock,
        mock_load: Mock,
        mock_save: Mock,
    ) -> None:
        """Test checking for updates with new filings."""
        mock_load.return_value = {
            "companies": {
                "AAPL": {
                    "name": "Apple Inc",
                    "watch_forms": ["10-K"],
                },
            },
            "last_check": None,
        }

        # Mock EDGAR client
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        company = Company(
            cik="123", ticker="AAPL", name="Apple", sic=None, sic_description=None, exchange=None
        )

        filing = Filing(
            accession_number="123",
            form_type="10-K",
            filing_date=date(2023, 11, 1),
            report_date=None,
            company=company,
            primary_document="test.htm",
            url="https://www.sec.gov/test",
        )

        mock_client.get_filings.return_value = [filing]

        result = check_watchlist_updates(days_back=7)

        assert result["success"] is True
        assert result["update_count"] == 1
        assert len(result["updates"]) == 1
        assert result["updates"][0]["ticker"] == "AAPL"
        assert result["updates"][0]["form_type"] == "10-K"

        # Verify last check was updated
        mock_save.assert_called_once()

    @patch("src.tools.watchlist._load_watchlist")
    def test_check_watchlist_updates_empty_watchlist(self, mock_load: Mock) -> None:
        """Test checking updates with empty watchlist."""
        mock_load.return_value = {"companies": {}, "last_check": None}

        result = check_watchlist_updates()

        assert result["success"] is True
        assert "empty" in result["message"].lower()
        assert result["updates"] == []

    @patch("src.tools.watchlist._save_watchlist")
    @patch("src.tools.watchlist._load_watchlist")
    @patch("src.tools.watchlist.get_edgar_client")
    def test_check_watchlist_updates_handles_errors(
        self,
        mock_get_client: Mock,
        mock_load: Mock,
        mock_save: Mock,
    ) -> None:
        """Test that individual company errors are caught."""
        mock_load.return_value = {
            "companies": {
                "AAPL": {"name": "Apple Inc", "watch_forms": ["10-K"]},
            },
            "last_check": None,
        }

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_filings.side_effect = Exception("API error")

        # Should not raise exception
        result = check_watchlist_updates()

        assert result["success"] is True
        assert result["update_count"] == 0


class TestGenerateWatchlistSummary:
    """Tests for generate_watchlist_summary function."""

    @patch("src.tools.watchlist._load_watchlist")
    @patch("src.tools.watchlist.get_edgar_client")
    def test_generate_watchlist_summary_with_data(
        self, mock_get_client: Mock, mock_load: Mock
    ) -> None:
        """Test generating summary with company data."""
        mock_load.return_value = {
            "companies": {
                "AAPL": {
                    "name": "Apple Inc",
                    "notes": "Tech giant",
                },
            },
            "last_check": None,
        }

        # Mock EDGAR client
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        company = Company(
            cik="123", ticker="AAPL", name="Apple", sic=None, sic_description=None, exchange=None
        )

        filing_10k = Filing(
            accession_number="123",
            form_type="10-K",
            filing_date=date(2023, 10, 27),
            report_date=None,
            company=company,
            primary_document="test.htm",
            url="https://www.sec.gov/test",
        )

        filing_8k = Filing(
            accession_number="456",
            form_type="8-K",
            filing_date=date(2023, 11, 1),
            report_date=None,
            company=company,
            primary_document="test2.htm",
            url="https://www.sec.gov/test2",
        )

        # Mock get_filings to return different results based on form_type
        def mock_get_filings(ticker, form_type, limit):
            if form_type == "10-K":
                return [filing_10k]
            elif form_type == "8-K":
                return [filing_8k]
            return []

        mock_client.get_filings.side_effect = mock_get_filings

        # Mock insider transactions
        insider = InsiderTransaction(
            insider_name="Tim Cook",
            insider_title="CEO",
            transaction_type="S",  # Sell
            transaction_date=date(2023, 11, 10),
            filing_date=date(2023, 11, 15),
            shares=10000.0,
            price_per_share=185.50,
            company=company,
            accession_number="789",
        )

        mock_client.get_insider_transactions.return_value = [insider]

        result = generate_watchlist_summary()

        assert result["success"] is True
        assert len(result["summaries"]) == 1

        summary = result["summaries"][0]
        assert summary["ticker"] == "AAPL"
        assert summary["name"] == "Apple Inc"
        assert summary["notes"] == "Tech giant"
        assert summary["latest_10k"]["date"] == "2023-10-27"
        assert summary["recent_8k_count"] == 1
        assert summary["insider_activity"]["sells"] == 1
        assert summary["insider_activity"]["sell_shares"] == 10000.0

    @patch("src.tools.watchlist._load_watchlist")
    def test_generate_watchlist_summary_empty(self, mock_load: Mock) -> None:
        """Test generating summary with empty watchlist."""
        mock_load.return_value = {"companies": {}, "last_check": None}

        result = generate_watchlist_summary()

        assert result["success"] is True
        assert "empty" in result["message"].lower()
        assert result["summaries"] == []

    @patch("src.tools.watchlist._load_watchlist")
    @patch("src.tools.watchlist.get_edgar_client")
    def test_generate_watchlist_summary_handles_errors(
        self, mock_get_client: Mock, mock_load: Mock
    ) -> None:
        """Test that errors for individual companies are handled."""
        mock_load.return_value = {
            "companies": {
                "INVALID": {"name": "Invalid Corp"},
            },
            "last_check": None,
        }

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_filings.side_effect = Exception("Company not found")

        result = generate_watchlist_summary()

        assert result["success"] is True
        assert len(result["summaries"]) == 1
        assert "error" in result["summaries"][0]

    @patch("src.tools.watchlist._load_watchlist")
    @patch("src.tools.watchlist.get_edgar_client")
    def test_generate_watchlist_summary_insider_buy_transactions(
        self, mock_get_client: Mock, mock_load: Mock
    ) -> None:
        """Test insider buy transactions are counted correctly."""
        mock_load.return_value = {
            "companies": {"TEST": {"name": "Test Corp"}},
            "last_check": None,
        }

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_filings.return_value = []

        company = Company(
            cik="123", ticker="TEST", name="Test", sic=None, sic_description=None, exchange=None
        )

        # Mock buy transaction
        insider_buy = InsiderTransaction(
            insider_name="Insider",
            insider_title="Director",
            transaction_type="P",  # Purchase
            transaction_date=date(2023, 11, 10),
            filing_date=date(2023, 11, 12),
            shares=5000.0,
            price_per_share=50.0,
            company=company,
            accession_number="123",
        )

        mock_client.get_insider_transactions.return_value = [insider_buy]

        result = generate_watchlist_summary()

        summary = result["summaries"][0]
        assert summary["insider_activity"]["buys"] == 1
        assert summary["insider_activity"]["buy_shares"] == 5000.0
        assert summary["insider_activity"]["sells"] == 0


class TestWatchlistToolsIntegration:
    """Integration tests (mark as slow)."""

    @pytest.mark.slow
    def test_watchlist_workflow_integration(self) -> None:
        """Test complete watchlist workflow."""
        # This would test against real SEC API
        # Skip for now as it requires actual infrastructure
        pass
