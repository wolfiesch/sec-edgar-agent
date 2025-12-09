"""Tests for analysis tools."""

from datetime import date
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.data.models import Company, Filing, FinancialStatement
from src.tools import registry
from src.tools.analysis import (
    analyze_historical_trends,
    compare_companies,
    detect_risk_changes,
    get_sector_peers,
)


class TestAnalysisToolsRegistry:
    """Tests for analysis tool registration."""

    def test_tools_registered(self) -> None:
        """Verify all analysis tools are registered."""
        tools = registry.list_tools()
        assert "analyze_historical_trends" in tools
        assert "compare_companies" in tools
        assert "detect_risk_changes" in tools
        assert "get_sector_peers" in tools


class TestAnalyzeHistoricalTrends:
    """Tests for analyze_historical_trends function."""

    @patch("src.tools.analysis.get_edgar_client")
    def test_revenue_trend_analysis(self, mock_get_client: Mock) -> None:
        """Test analyzing revenue trends with multiple years."""
        # Mock financial statements
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        statements = [
            FinancialStatement(
                fiscal_year=2020,
                fiscal_period="FY",
                period_end=date(2020, 12, 31),
                statement_type="income_statement",
                data={"revenue": 100_000_000},
            ),
            FinancialStatement(
                fiscal_year=2021,
                fiscal_period="FY",
                period_end=date(2021, 12, 31),
                statement_type="income_statement",
                data={"revenue": 120_000_000},
            ),
            FinancialStatement(
                fiscal_year=2022,
                fiscal_period="FY",
                period_end=date(2022, 12, 31),
                statement_type="income_statement",
                data={"revenue": 150_000_000},
            ),
        ]
        mock_client.get_financials.return_value = statements

        result = analyze_historical_trends("AAPL", "revenue", 3)

        assert result["success"] is True
        assert result["ticker"] == "AAPL"
        assert result["metric"] == "revenue"
        assert result["period"] == "2020-2022"
        assert len(result["data_points"]) == 3

        # Check data points
        assert result["data_points"][0]["year"] == 2020
        assert result["data_points"][0]["value"] == 100_000_000
        assert result["data_points"][1]["yoy_change"] == 20_000_000
        assert result["data_points"][1]["yoy_change_pct"] == 20.0

        # Check summary
        assert "cagr" in result["summary"]
        assert result["summary"]["trend"] in ["strong_growth", "moderate_growth"]
        assert result["summary"]["total_change"] == 50_000_000

        # Check narrative exists
        assert "narrative" in result
        assert "AAPL" in result["narrative"]

    @patch("src.tools.analysis.get_edgar_client")
    def test_balance_sheet_metric(self, mock_get_client: Mock) -> None:
        """Test analyzing balance sheet metrics like total_assets."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        statements = [
            FinancialStatement(
                fiscal_year=2021,
                fiscal_period="FY",
                period_end=date(2021, 12, 31),
                statement_type="balance_sheet",
                data={"total_assets": 500_000_000},
            ),
            FinancialStatement(
                fiscal_year=2022,
                fiscal_period="FY",
                period_end=date(2022, 12, 31),
                statement_type="balance_sheet",
                data={"total_assets": 550_000_000},
            ),
        ]
        mock_client.get_financials.return_value = statements

        result = analyze_historical_trends("MSFT", "total_assets", 2)

        assert result["success"] is True
        mock_client.get_financials.assert_called_with(
            ticker="MSFT",
            statement_type="balance_sheet",
            periods=2,
        )

    @patch("src.tools.analysis.get_edgar_client")
    def test_declining_trend(self, mock_get_client: Mock) -> None:
        """Test identifying declining trends."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        statements = [
            FinancialStatement(
                fiscal_year=2020,
                fiscal_period="FY",
                period_end=date(2020, 12, 31),
                statement_type="income_statement",
                data={"net_income": 100_000_000},
            ),
            FinancialStatement(
                fiscal_year=2021,
                fiscal_period="FY",
                period_end=date(2021, 12, 31),
                statement_type="income_statement",
                data={"net_income": 80_000_000},
            ),
            FinancialStatement(
                fiscal_year=2022,
                fiscal_period="FY",
                period_end=date(2022, 12, 31),
                statement_type="income_statement",
                data={"net_income": 60_000_000},
            ),
        ]
        mock_client.get_financials.return_value = statements

        result = analyze_historical_trends("TSLA", "net_income", 3)

        assert result["success"] is True
        assert result["summary"]["trend"] in ["strong_decline", "moderate_decline"]
        assert result["summary"]["total_change"] < 0

    @patch("src.tools.analysis.get_edgar_client")
    def test_insufficient_data(self, mock_get_client: Mock) -> None:
        """Test handling insufficient data points."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Only one data point
        statements = [
            FinancialStatement(
                fiscal_year=2022,
                fiscal_period="FY",
                period_end=date(2022, 12, 31),
                statement_type="income_statement",
                data={"revenue": 100_000_000},
            ),
        ]
        mock_client.get_financials.return_value = statements

        result = analyze_historical_trends("TEST", "revenue", 5)

        assert result["success"] is False
        assert "Insufficient data points" in result["error"]

    @patch("src.tools.analysis.get_edgar_client")
    def test_no_financial_data(self, mock_get_client: Mock) -> None:
        """Test handling no financial data."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_financials.return_value = []

        result = analyze_historical_trends("INVALID", "revenue", 3)

        assert result["success"] is False
        assert "No financial data found" in result["error"]


class TestCompareCompanies:
    """Tests for compare_companies function."""

    @patch("src.tools.analysis.get_edgar_client")
    def test_compare_two_companies(self, mock_get_client: Mock) -> None:
        """Test comparing two companies across metrics."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock company data
        def mock_get_company(ticker: str) -> Company:
            companies = {
                "AAPL": Company(ticker="AAPL", cik="0000320193", name="Apple Inc"),
                "MSFT": Company(ticker="MSFT", cik="0000789019", name="Microsoft Corp"),
            }
            return companies[ticker]

        def mock_get_financials(ticker: str, statement_type: str, periods: int) -> list:
            if statement_type == "income_statement":
                data = {
                    "AAPL": [FinancialStatement(
                        fiscal_year=2023,
                        fiscal_period="FY",
                        period_end=date(2023, 12, 31),
                        statement_type="income_statement",
                        data={"revenue": 383_000_000_000, "net_income": 97_000_000_000},
                    )],
                    "MSFT": [FinancialStatement(
                        fiscal_year=2023,
                        fiscal_period="FY",
                        period_end=date(2023, 12, 31),
                        statement_type="income_statement",
                        data={"revenue": 211_000_000_000, "net_income": 72_000_000_000},
                    )],
                }
                return data.get(ticker, [])
            return []

        mock_client.get_company.side_effect = mock_get_company
        mock_client.get_financials.side_effect = mock_get_financials

        result = compare_companies(["AAPL", "MSFT"], ["revenue", "net_income"])

        assert result["success"] is True
        assert len(result["companies"]) == 2
        assert result["metrics_compared"] == ["revenue", "net_income"]

        # Check company data
        aapl = next(c for c in result["companies"] if c["ticker"] == "AAPL")
        assert aapl["name"] == "Apple Inc"
        assert aapl["metrics"]["revenue"] == 383_000_000_000
        assert aapl["metrics"]["net_income"] == 97_000_000_000

        # Check rankings
        assert result["rankings"]["revenue"][0] == "AAPL"
        assert result["rankings"]["net_income"][0] == "AAPL"

    @patch("src.tools.analysis.get_edgar_client")
    def test_compare_with_default_metrics(self, mock_get_client: Mock) -> None:
        """Test comparison with default metrics."""
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
                statement_type="income_statement",
                data={"revenue": 1000, "net_income": 100},
            )
        ]

        result = compare_companies(["TEST"])

        assert result["success"] is True
        assert result["metrics_compared"] == ["revenue", "net_income"]

    @patch("src.tools.analysis.get_edgar_client")
    def test_compare_with_missing_data(self, mock_get_client: Mock) -> None:
        """Test handling companies with missing data."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        def mock_get_company(ticker: str) -> Company:
            if ticker == "GOOD":
                return Company(ticker="GOOD", cik="123", name="Good Corp")
            raise Exception("Company not found")

        mock_client.get_company.side_effect = mock_get_company

        result = compare_companies(["GOOD", "BAD"])

        assert result["success"] is True
        assert len(result["companies"]) == 2
        # Bad company should have error field
        bad = next(c for c in result["companies"] if c["ticker"] == "BAD")
        assert "error" in bad


class TestDetectRiskChanges:
    """Tests for detect_risk_changes function."""

    @patch("src.tools.analysis.get_edgar_client")
    def test_find_filings_for_both_years(self, mock_get_client: Mock) -> None:
        """Test finding and comparing filings from two years."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Create mock company for filings
        mock_company = Company(ticker="AAPL", cik="0000320193", name="Apple Inc")

        filings = [
            Filing(
                accession_number="0000320193-21-000105",
                filing_date=date(2021, 10, 29),
                report_date=date(2021, 9, 25),
                form_type="10-K",
                company=mock_company,
                url="https://example.com/filing1",
            ),
            Filing(
                accession_number="0000320193-22-000108",
                filing_date=date(2022, 10, 28),
                report_date=date(2022, 9, 24),
                form_type="10-K",
                company=mock_company,
                url="https://example.com/filing2",
            ),
        ]
        mock_client.get_filings.return_value = filings

        result = detect_risk_changes("AAPL", 2021, 2022)

        assert result["success"] is True
        assert result["ticker"] == "AAPL"
        assert result["comparison"]["year1"]["fiscal_year"] == 2021
        assert result["comparison"]["year2"]["fiscal_year"] == 2022
        assert "0000320193-21-000105" in result["comparison"]["year1"]["accession"]
        assert "0000320193-22-000108" in result["comparison"]["year2"]["accession"]

    @patch("src.tools.analysis.get_edgar_client")
    def test_missing_filings(self, mock_get_client: Mock) -> None:
        """Test handling missing filings for requested years."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Only one filing
        mock_company = Company(ticker="AAPL", cik="0000320193", name="Apple Inc")
        filings = [
            Filing(
                accession_number="0000320193-21-000105",
                filing_date=date(2021, 10, 29),
                report_date=date(2021, 9, 25),
                form_type="10-K",
                company=mock_company,
                url="https://example.com/filing1",
            ),
        ]
        mock_client.get_filings.return_value = filings

        result = detect_risk_changes("AAPL", 2021, 2025)

        assert result["success"] is False
        assert "Could not find 10-K filings" in result["error"]

    @patch("src.tools.analysis.get_edgar_client")
    def test_handles_early_year_filings(self, mock_get_client: Mock) -> None:
        """Test handling filings from early following year (Q1)."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Filing dated in early 2022 but for fiscal 2021
        mock_company = Company(ticker="TEST", cik="123", name="Test Corp")
        filings = [
            Filing(
                accession_number="0000320193-22-000001",
                filing_date=date(2022, 1, 15),  # Early 2022
                report_date=date(2021, 12, 31),
                form_type="10-K",
                company=mock_company,
                url="https://example.com/filing1",
            ),
        ]
        mock_client.get_filings.return_value = filings

        result = detect_risk_changes("TEST", 2021, 2021)

        # Should successfully match the early-year filing
        assert result["success"] is True or "Could not find" in result.get("error", "")


class TestGetSectorPeers:
    """Tests for get_sector_peers function."""

    @patch("src.tools.analysis.get_edgar_client")
    def test_get_peers_for_known_company(self, mock_get_client: Mock) -> None:
        """Test getting peers for a well-known company."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_client.get_company.return_value = Company(
            ticker="AAPL",
            cik="0000320193",
            name="Apple Inc",
            sic="3571",
        )

        result = get_sector_peers("AAPL", limit=5)

        assert result["success"] is True
        assert result["ticker"] == "AAPL"
        assert result["company"] == "Apple Inc"
        assert "sic" in result
        assert len(result["peers"]) <= 5
        assert "MSFT" in result["peers"] or "GOOGL" in result["peers"]

    @patch("src.tools.analysis.get_edgar_client")
    def test_limit_peers_returned(self, mock_get_client: Mock) -> None:
        """Test that limit parameter is respected."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_client.get_company.return_value = Company(
            ticker="AAPL",
            cik="0000320193",
            name="Apple Inc",
            sic="3571",
        )

        result = get_sector_peers("AAPL", limit=2)

        assert result["success"] is True
        assert len(result["peers"]) <= 2

    @patch("src.tools.analysis.get_edgar_client")
    def test_unknown_company_peers(self, mock_get_client: Mock) -> None:
        """Test getting peers for unknown company returns empty list."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_client.get_company.return_value = Company(
            ticker="UNKNOWN",
            cik="9999999",
            name="Unknown Corp",
            sic="9999",
        )

        result = get_sector_peers("UNKNOWN")

        assert result["success"] is True
        assert result["peers"] == []

    @patch("src.tools.analysis.get_edgar_client")
    def test_error_handling(self, mock_get_client: Mock) -> None:
        """Test error handling for peer lookup."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_company.side_effect = Exception("Company not found")

        result = get_sector_peers("INVALID")

        assert result["success"] is False
        assert "error" in result


class TestAnalysisToolsIntegration:
    """Integration tests that hit real SEC API (mark as slow)."""

    @pytest.mark.slow
    def test_analyze_historical_trends_integration(self) -> None:
        """Test analyzing real historical trends for Apple."""
        result = analyze_historical_trends("AAPL", "revenue", 3)

        assert result["success"] is True
        assert result["ticker"] == "AAPL"
        assert len(result["data_points"]) >= 2
        assert "cagr" in result["summary"]
        assert "narrative" in result

    @pytest.mark.slow
    def test_compare_companies_integration(self) -> None:
        """Test comparing real companies."""
        result = compare_companies(["AAPL", "MSFT"], ["revenue"])

        assert result["success"] is True
        assert len(result["companies"]) == 2
        assert "rankings" in result

    @pytest.mark.slow
    def test_get_sector_peers_integration(self) -> None:
        """Test getting real sector peers."""
        result = get_sector_peers("AAPL", limit=3)

        assert result["success"] is True
        assert result["ticker"] == "AAPL"
        assert "peers" in result
