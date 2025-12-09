"""Tests for financial data extraction tools."""

from datetime import date
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.data.models import Company, FinancialStatement, InsiderTransaction
from src.tools import registry
from src.tools.financials import (
    compare_financials,
    get_balance_sheet,
    get_cash_flow,
    get_income_statement,
    get_insider_trades,
)


class TestFinancialsToolsRegistry:
    """Tests for financials tool registration."""

    def test_tools_registered(self) -> None:
        """Verify all financials tools are registered."""
        tools = registry.list_tools()
        assert "get_income_statement" in tools
        assert "get_balance_sheet" in tools
        assert "get_cash_flow" in tools
        assert "get_insider_trades" in tools
        assert "compare_financials" in tools


class TestGetIncomeStatement:
    """Tests for get_income_statement function."""

    @patch("src.tools.financials.get_edgar_client")
    def test_get_income_statement_success(self, mock_get_client: Mock) -> None:
        """Test successfully retrieving income statement data."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        statements = [
            FinancialStatement(
                fiscal_year=2023,
                fiscal_period="FY",
                period_end=date(2023, 12, 31),
                statement_type="income_statement",
                currency="USD",
                data={
                    "revenue": 383_000_000_000,
                    "net_income": 97_000_000_000,
                    "gross_profit": 170_000_000_000,
                },
            ),
            FinancialStatement(
                fiscal_year=2022,
                fiscal_period="FY",
                period_end=date(2022, 12, 31),
                statement_type="income_statement",
                currency="USD",
                data={
                    "revenue": 365_000_000_000,
                    "net_income": 94_000_000_000,
                    "gross_profit": 160_000_000_000,
                },
            ),
        ]
        mock_client.get_financials.return_value = statements

        result = get_income_statement("AAPL", 2)

        assert result["success"] is True
        assert result["ticker"] == "AAPL"
        assert result["periods"] == 2
        assert len(result["statements"]) == 2

        # Check first statement
        stmt = result["statements"][0]
        assert stmt["fiscal_year"] == 2023
        assert stmt["currency"] == "USD"
        assert stmt["data"]["revenue"] == 383_000_000_000
        assert stmt["data"]["net_income"] == 97_000_000_000

        # Check citations
        assert "citations" in result
        assert len(result["citations"]) == 2

    @patch("src.tools.financials.get_edgar_client")
    def test_get_income_statement_default_periods(self, mock_get_client: Mock) -> None:
        """Test using default periods parameter."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_financials.return_value = [
            FinancialStatement(
                fiscal_year=2023,
                fiscal_period="FY",
                period_end=date(2023, 12, 31),
                statement_type="income_statement",
                currency="USD",
                data={"revenue": 1000},
            )
        ]

        result = get_income_statement("MSFT")

        assert result["success"] is True
        mock_client.get_financials.assert_called_with(
            ticker="MSFT",
            statement_type="income_statement",
            periods=3,
        )

    @patch("src.tools.financials.get_edgar_client")
    def test_get_income_statement_no_data(self, mock_get_client: Mock) -> None:
        """Test handling no data found."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_financials.return_value = []

        result = get_income_statement("INVALID")

        assert result["success"] is False
        assert "No income statement data found" in result["error"]

    @patch("src.tools.financials.get_edgar_client")
    def test_get_income_statement_error(self, mock_get_client: Mock) -> None:
        """Test handling errors during data retrieval."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_financials.side_effect = Exception("API error")

        result = get_income_statement("TEST")

        assert result["success"] is False
        assert "API error" in result["error"]


class TestGetBalanceSheet:
    """Tests for get_balance_sheet function."""

    @patch("src.tools.financials.get_edgar_client")
    def test_get_balance_sheet_success(self, mock_get_client: Mock) -> None:
        """Test successfully retrieving balance sheet data."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        statements = [
            FinancialStatement(
                fiscal_year=2023,
                fiscal_period="FY",
                period_end=date(2023, 12, 31),
                statement_type="balance_sheet",
                currency="USD",
                data={
                    "total_assets": 352_000_000_000,
                    "total_liabilities": 290_000_000_000,
                    "stockholders_equity": 62_000_000_000,
                },
            ),
        ]
        mock_client.get_financials.return_value = statements

        result = get_balance_sheet("AAPL", 1)

        assert result["success"] is True
        assert result["ticker"] == "AAPL"
        assert result["periods"] == 1
        assert len(result["statements"]) == 1

        # Check data
        stmt = result["statements"][0]
        assert stmt["data"]["total_assets"] == 352_000_000_000
        assert stmt["data"]["stockholders_equity"] == 62_000_000_000

    @patch("src.tools.financials.get_edgar_client")
    def test_get_balance_sheet_multiple_periods(self, mock_get_client: Mock) -> None:
        """Test retrieving multiple periods."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        statements = [
            FinancialStatement(
                fiscal_year=year,
                fiscal_period="FY",
                period_end=date(year, 12, 31),
                statement_type="balance_sheet",
                currency="USD",
                data={"total_assets": 100_000_000 * year},
            )
            for year in [2023, 2022, 2021]
        ]
        mock_client.get_financials.return_value = statements

        result = get_balance_sheet("TEST", 3)

        assert result["success"] is True
        assert result["periods"] == 3
        assert len(result["statements"]) == 3

    @patch("src.tools.financials.get_edgar_client")
    def test_get_balance_sheet_no_data(self, mock_get_client: Mock) -> None:
        """Test handling no data found."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_financials.return_value = []

        result = get_balance_sheet("INVALID")

        assert result["success"] is False
        assert "No balance sheet data found" in result["error"]


class TestGetCashFlow:
    """Tests for get_cash_flow function."""

    @patch("src.tools.financials.get_edgar_client")
    def test_get_cash_flow_success(self, mock_get_client: Mock) -> None:
        """Test successfully retrieving cash flow data."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        statements = [
            FinancialStatement(
                fiscal_year=2023,
                fiscal_period="FY",
                period_end=date(2023, 12, 31),
                statement_type="cash_flow",
                currency="USD",
                data={
                    "operating_cash_flow": 110_000_000_000,
                    "investing_cash_flow": -10_000_000_000,
                    "financing_cash_flow": -90_000_000_000,
                },
            ),
        ]
        mock_client.get_financials.return_value = statements

        result = get_cash_flow("AAPL", 1)

        assert result["success"] is True
        assert result["ticker"] == "AAPL"
        assert result["periods"] == 1

        # Check cash flow data
        stmt = result["statements"][0]
        assert stmt["data"]["operating_cash_flow"] == 110_000_000_000
        assert stmt["data"]["investing_cash_flow"] == -10_000_000_000

    @patch("src.tools.financials.get_edgar_client")
    def test_get_cash_flow_no_data(self, mock_get_client: Mock) -> None:
        """Test handling no data found."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_financials.return_value = []

        result = get_cash_flow("INVALID")

        assert result["success"] is False
        assert "No cash flow data found" in result["error"]

    @patch("src.tools.financials.get_edgar_client")
    def test_get_cash_flow_error(self, mock_get_client: Mock) -> None:
        """Test handling errors."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_financials.side_effect = Exception("Connection error")

        result = get_cash_flow("TEST")

        assert result["success"] is False
        assert "Connection error" in result["error"]


class TestGetInsiderTrades:
    """Tests for get_insider_trades function."""

    @patch("src.tools.financials.get_edgar_client")
    def test_get_insider_trades_success(self, mock_get_client: Mock) -> None:
        """Test successfully retrieving insider transactions."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_company = Company(ticker="AAPL", cik="0000320193", name="Apple Inc")

        transactions = [
            InsiderTransaction(
                accession_number="0001234567-23-000001",
                filing_date=date(2023, 11, 15),
                company=mock_company,
                insider_name="Tim Cook",
                insider_title="CEO",
                transaction_date=date(2023, 11, 10),
                transaction_type="S",
                shares=10000,
                price_per_share=185.50,
                total_value=1_855_000,
                shares_owned_after=3_000_000,
            ),
            InsiderTransaction(
                accession_number="0001234567-23-000002",
                filing_date=date(2023, 11, 20),
                company=mock_company,
                insider_name="Tim Cook",
                insider_title="CEO",
                transaction_date=date(2023, 11, 18),
                transaction_type="P",
                shares=5000,
                price_per_share=180.00,
                total_value=900_000,
                shares_owned_after=3_005_000,
            ),
            InsiderTransaction(
                accession_number="0001234567-23-000003",
                filing_date=date(2023, 11, 25),
                company=mock_company,
                insider_name="Luca Maestri",
                insider_title="CFO",
                transaction_date=date(2023, 11, 22),
                transaction_type="P",
                shares=2000,
                price_per_share=182.00,
                total_value=364_000,
                shares_owned_after=500_000,
            ),
        ]
        mock_client.get_insider_transactions.return_value = transactions

        result = get_insider_trades("AAPL", 20)

        assert result["success"] is True
        assert result["ticker"] == "AAPL"
        assert result["transaction_count"] == 3
        assert len(result["by_insider"]) == 2

        # Check Tim Cook's summary
        tim = next(i for i in result["by_insider"] if i["name"] == "Tim Cook")
        assert tim["title"] == "CEO"
        assert tim["total_bought"] == 5000
        assert tim["total_sold"] == 10000
        assert len(tim["transactions"]) == 2

        # Check transaction details
        sell_txn = next(t for t in tim["transactions"] if t["type"] == "Sell")
        assert sell_txn["shares"] == 10000
        assert sell_txn["price"] == 185.50

    @patch("src.tools.financials.get_edgar_client")
    def test_get_insider_trades_no_transactions(self, mock_get_client: Mock) -> None:
        """Test handling no insider transactions found."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_insider_transactions.return_value = []

        result = get_insider_trades("SMALL", 20)

        assert result["success"] is True
        assert result["ticker"] == "SMALL"
        assert "No recent insider transactions found" in result["message"]
        assert result["transactions"] == []

    @patch("src.tools.financials.get_edgar_client")
    def test_get_insider_trades_limit(self, mock_get_client: Mock) -> None:
        """Test limit parameter is passed correctly."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_insider_transactions.return_value = []

        get_insider_trades("TEST", 10)

        mock_client.get_insider_transactions.assert_called_with("TEST", 10)

    @patch("src.tools.financials.get_edgar_client")
    def test_get_insider_trades_error(self, mock_get_client: Mock) -> None:
        """Test handling errors."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_insider_transactions.side_effect = Exception("API failure")

        result = get_insider_trades("TEST")

        assert result["success"] is False
        assert "API failure" in result["error"]


class TestCompareFinancials:
    """Tests for compare_financials function."""

    @patch("src.tools.financials.get_edgar_client")
    def test_compare_financials_revenue(self, mock_get_client: Mock) -> None:
        """Test comparing revenue across companies."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        def mock_get_company(ticker: str) -> Company:
            companies = {
                "AAPL": Company(ticker="AAPL", cik="0000320193", name="Apple Inc"),
                "MSFT": Company(ticker="MSFT", cik="0000789019", name="Microsoft Corp"),
            }
            return companies[ticker]

        def mock_get_financials(ticker: str, statement_type: str, periods: int) -> list:
            data = {
                "AAPL": [
                    FinancialStatement(
                        fiscal_year=2023,
                        fiscal_period="FY",
                        period_end=date(2023, 12, 31),
                        statement_type="income_statement",
                        data={"revenue": 383_000_000_000},
                    )
                ],
                "MSFT": [
                    FinancialStatement(
                        fiscal_year=2023,
                        fiscal_period="FY",
                        period_end=date(2023, 12, 31),
                        statement_type="income_statement",
                        data={"revenue": 211_000_000_000},
                    )
                ],
            }
            return data.get(ticker, [])

        mock_client.get_company.side_effect = mock_get_company
        mock_client.get_financials.side_effect = mock_get_financials

        result = compare_financials(["AAPL", "MSFT"], "revenue")

        assert result["success"] is True
        assert result["metric"] == "revenue"
        assert len(result["companies"]) == 2

        # Check sorted order (descending by value)
        assert result["companies"][0]["ticker"] == "AAPL"
        assert result["companies"][0]["value"] == 383_000_000_000
        assert result["companies"][1]["ticker"] == "MSFT"
        assert result["companies"][1]["value"] == 211_000_000_000

    @patch("src.tools.financials.get_edgar_client")
    def test_compare_financials_balance_sheet_metric(self, mock_get_client: Mock) -> None:
        """Test comparing balance sheet metrics."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_client.get_company.return_value = Company(
            ticker="TEST", cik="123", name="Test Corp"
        )
        mock_client.get_financials.return_value = [
            FinancialStatement(
                fiscal_year=2023,
                fiscal_period="FY",
                period_end=date(2023, 12, 31),
                statement_type="balance_sheet",
                data={"total_assets": 500_000_000},
            )
        ]

        result = compare_financials(["TEST", "TEST2"], "total_assets")

        assert result["success"] is True
        assert result["metric"] == "total_assets"
        # Should fetch balance_sheet, not income_statement
        calls = mock_client.get_financials.call_args_list
        assert any("balance_sheet" in str(call) for call in calls)

    @patch("src.tools.financials.get_edgar_client")
    def test_compare_financials_missing_data(self, mock_get_client: Mock) -> None:
        """Test handling companies with missing data."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        def mock_get_company(ticker: str) -> Company:
            if ticker == "GOOD":
                return Company(ticker="GOOD", cik="123", name="Good Corp")
            raise Exception("Company not found")

        def mock_get_financials(ticker: str, statement_type: str, periods: int) -> list:
            if ticker == "GOOD":
                return [
                    FinancialStatement(
                        fiscal_year=2023,
                        fiscal_period="FY",
                        period_end=date(2023, 12, 31),
                        statement_type="income_statement",
                        data={"revenue": 1_000_000},
                    )
                ]
            return []

        mock_client.get_company.side_effect = mock_get_company
        mock_client.get_financials.side_effect = mock_get_financials

        result = compare_financials(["GOOD", "BAD"], "revenue")

        assert result["success"] is True
        assert len(result["companies"]) == 2

        # BAD company should have error field
        bad = next(c for c in result["companies"] if c["ticker"] == "BAD")
        assert "error" in bad

    @patch("src.tools.financials.get_edgar_client")
    def test_compare_financials_null_values(self, mock_get_client: Mock) -> None:
        """Test handling null/missing metric values."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_client.get_company.return_value = Company(
            ticker="TEST", cik="123", name="Test Corp"
        )
        # Return statement with empty data dict
        mock_client.get_financials.return_value = [
            FinancialStatement(
                fiscal_year=2023,
                fiscal_period="FY",
                period_end=date(2023, 12, 31),
                statement_type="income_statement",
                data={},  # Missing the requested metric
            )
        ]

        result = compare_financials(["TEST"], "revenue")

        assert result["success"] is True
        assert result["companies"][0]["value"] is None


class TestFinancialsToolsIntegration:
    """Integration tests that hit real SEC API (mark as slow)."""

    @pytest.mark.slow
    def test_get_income_statement_integration(self) -> None:
        """Test getting real income statement for Apple."""
        result = get_income_statement("AAPL", 2)

        assert result["success"] is True
        assert result["ticker"] == "AAPL"
        assert result["periods"] >= 1
        assert len(result["statements"]) >= 1

        # Check data structure
        stmt = result["statements"][0]
        assert "fiscal_year" in stmt
        assert "data" in stmt
        assert isinstance(stmt["data"], dict)

    @pytest.mark.slow
    def test_get_balance_sheet_integration(self) -> None:
        """Test getting real balance sheet for Microsoft."""
        result = get_balance_sheet("MSFT", 1)

        assert result["success"] is True
        assert result["ticker"] == "MSFT"
        assert len(result["statements"]) >= 1

    @pytest.mark.slow
    def test_get_cash_flow_integration(self) -> None:
        """Test getting real cash flow for Apple."""
        result = get_cash_flow("AAPL", 1)

        assert result["success"] is True
        assert result["ticker"] == "AAPL"
        assert len(result["statements"]) >= 1

    @pytest.mark.slow
    def test_compare_financials_integration(self) -> None:
        """Test comparing real companies."""
        result = compare_financials(["AAPL", "MSFT"], "revenue")

        assert result["success"] is True
        assert len(result["companies"]) == 2
        assert result["metric"] == "revenue"
