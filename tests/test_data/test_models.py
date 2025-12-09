"""Tests for Pydantic data models."""

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from src.data.models import (
    AgentMessage,
    Citation,
    Company,
    Filing,
    FilingSection,
    FinancialStatement,
    InsiderTransaction,
    ToolResult,
)


class TestCompanyModel:
    """Tests for Company model."""

    def test_company_minimal(self) -> None:
        """Test creating a company with minimal required fields."""
        company = Company(cik="0000320193", ticker="AAPL", name="Apple Inc.")
        assert company.cik == "0000320193"
        assert company.ticker == "AAPL"
        assert company.name == "Apple Inc."
        assert company.sic is None
        assert company.sic_description is None
        assert company.exchange is None

    def test_company_full(self) -> None:
        """Test creating a company with all fields."""
        company = Company(
            cik="0000320193",
            ticker="AAPL",
            name="Apple Inc.",
            sic="3571",
            sic_description="Electronic Computers",
            exchange="NASDAQ",
        )
        assert company.sic == "3571"
        assert company.sic_description == "Electronic Computers"
        assert company.exchange == "NASDAQ"

    def test_company_missing_required_field(self) -> None:
        """Test that missing required fields raise validation error."""
        with pytest.raises(ValidationError) as exc_info:
            Company(cik="0000320193", ticker="AAPL")  # Missing name

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("name",) for e in errors)


class TestFilingModel:
    """Tests for Filing model."""

    def test_filing_minimal(self) -> None:
        """Test creating a filing with minimal fields."""
        company = Company(cik="0000320193", ticker="AAPL", name="Apple Inc.")
        filing = Filing(
            accession_number="0000320193-24-000123",
            form_type="10-K",
            filing_date=date(2024, 10, 31),
            company=company,
        )
        assert filing.accession_number == "0000320193-24-000123"
        assert filing.form_type == "10-K"
        assert filing.filing_date == date(2024, 10, 31)
        assert filing.report_date is None
        assert filing.primary_document is None
        assert filing.url is None

    def test_filing_full(self) -> None:
        """Test creating a filing with all fields."""
        company = Company(cik="0000320193", ticker="AAPL", name="Apple Inc.")
        filing = Filing(
            accession_number="0000320193-24-000123",
            form_type="10-K",
            filing_date=date(2024, 10, 31),
            report_date=date(2024, 9, 30),
            company=company,
            primary_document="aapl-20240930.htm",
            url="https://www.sec.gov/Archives/edgar/data/320193/0000320193-24-000123",
        )
        assert filing.report_date == date(2024, 9, 30)
        assert filing.primary_document == "aapl-20240930.htm"
        assert filing.url is not None


class TestFinancialStatementModel:
    """Tests for FinancialStatement model."""

    def test_financial_statement(self) -> None:
        """Test creating a financial statement."""
        stmt = FinancialStatement(
            statement_type="income_statement",
            period_end=date(2024, 9, 30),
            fiscal_year=2024,
            fiscal_period="Q4",
            data={
                "Revenue": 100000000,
                "NetIncome": 25000000,
            },
        )
        assert stmt.statement_type == "income_statement"
        assert stmt.fiscal_year == 2024
        assert stmt.fiscal_period == "Q4"
        assert stmt.currency == "USD"  # Default
        assert stmt.data["Revenue"] == 100000000

    def test_financial_statement_custom_currency(self) -> None:
        """Test with custom currency."""
        stmt = FinancialStatement(
            statement_type="balance_sheet",
            period_end=date(2024, 9, 30),
            fiscal_year=2024,
            fiscal_period="FY",
            currency="EUR",
            data={},
        )
        assert stmt.currency == "EUR"


class TestFilingSectionModel:
    """Tests for FilingSection model."""

    def test_filing_section_minimal(self) -> None:
        """Test creating a filing section with minimal fields."""
        section = FilingSection(
            filing_accession="0000320193-24-000123",
            section_name="Risk Factors",
            content="Risk factor content...",
        )
        assert section.filing_accession == "0000320193-24-000123"
        assert section.section_name == "Risk Factors"
        assert section.content == "Risk factor content..."
        assert section.section_number is None
        assert section.page_start is None
        assert section.page_end is None

    def test_filing_section_full(self) -> None:
        """Test creating a filing section with all fields."""
        section = FilingSection(
            filing_accession="0000320193-24-000123",
            section_name="Risk Factors",
            section_number="Item 1A",
            content="Risk factor content...",
            page_start=15,
            page_end=25,
        )
        assert section.section_number == "Item 1A"
        assert section.page_start == 15
        assert section.page_end == 25


class TestInsiderTransactionModel:
    """Tests for InsiderTransaction model."""

    def test_insider_transaction_minimal(self) -> None:
        """Test creating insider transaction with minimal fields."""
        company = Company(cik="0000320193", ticker="AAPL", name="Apple Inc.")
        transaction = InsiderTransaction(
            accession_number="0001127602-24-000001",
            filing_date=date(2024, 11, 15),
            company=company,
            insider_name="Tim Cook",
            transaction_date=date(2024, 11, 10),
            transaction_type="S",
            shares=10000,
        )
        assert transaction.insider_name == "Tim Cook"
        assert transaction.transaction_type == "S"
        assert transaction.shares == 10000
        assert transaction.insider_title is None
        assert transaction.price_per_share is None

    def test_insider_transaction_full(self) -> None:
        """Test creating insider transaction with all fields."""
        company = Company(cik="0000320193", ticker="AAPL", name="Apple Inc.")
        transaction = InsiderTransaction(
            accession_number="0001127602-24-000001",
            filing_date=date(2024, 11, 15),
            company=company,
            insider_name="Tim Cook",
            insider_title="CEO",
            transaction_date=date(2024, 11, 10),
            transaction_type="S",
            shares=10000,
            price_per_share=180.50,
            total_value=1805000.00,
            shares_owned_after=3000000,
        )
        assert transaction.insider_title == "CEO"
        assert transaction.price_per_share == 180.50
        assert transaction.total_value == 1805000.00
        assert transaction.shares_owned_after == 3000000


class TestCitationModel:
    """Tests for Citation model."""

    def test_citation_minimal(self) -> None:
        """Test creating a citation with minimal fields."""
        citation = Citation(
            ticker="AAPL",
            form_type="10-K",
            filing_date=date(2024, 10, 31),
            accession_number="0000320193-24-000123",
        )
        assert citation.ticker == "AAPL"
        assert citation.form_type == "10-K"
        assert citation.section is None
        assert citation.page is None

    def test_citation_full(self) -> None:
        """Test creating a citation with all fields."""
        citation = Citation(
            ticker="AAPL",
            form_type="10-K",
            filing_date=date(2024, 10, 31),
            accession_number="0000320193-24-000123",
            section="Risk Factors",
            page=42,
        )
        assert citation.section == "Risk Factors"
        assert citation.page == 42

    def test_citation_str_minimal(self) -> None:
        """Test citation string representation without section/page."""
        citation = Citation(
            ticker="AAPL",
            form_type="10-K",
            filing_date=date(2024, 10, 31),
            accession_number="0000320193-24-000123",
        )
        assert str(citation) == "[AAPL, 10-K, 2024]"

    def test_citation_str_with_section(self) -> None:
        """Test citation string with section."""
        citation = Citation(
            ticker="AAPL",
            form_type="10-K",
            filing_date=date(2024, 10, 31),
            accession_number="0000320193-24-000123",
            section="Risk Factors",
        )
        assert str(citation) == "[AAPL, 10-K, 2024, Risk Factors]"

    def test_citation_str_with_page(self) -> None:
        """Test citation string with section and page."""
        citation = Citation(
            ticker="AAPL",
            form_type="10-K",
            filing_date=date(2024, 10, 31),
            accession_number="0000320193-24-000123",
            section="Item 7",
            page=45,
        )
        assert str(citation) == "[AAPL, 10-K, 2024, Item 7, p.45]"


class TestAgentMessageModel:
    """Tests for AgentMessage model."""

    def test_agent_message_minimal(self) -> None:
        """Test creating an agent message with minimal fields."""
        msg = AgentMessage(role="user", content="What is Apple's revenue?")
        assert msg.role == "user"
        assert msg.content == "What is Apple's revenue?"
        assert isinstance(msg.timestamp, datetime)
        assert msg.tool_use_id is None
        assert msg.citations == []

    def test_agent_message_with_citations(self) -> None:
        """Test agent message with citations."""
        citation = Citation(
            ticker="AAPL",
            form_type="10-K",
            filing_date=date(2024, 10, 31),
            accession_number="0000320193-24-000123",
        )
        msg = AgentMessage(
            role="assistant",
            content="Apple's revenue was $100B",
            citations=[citation],
        )
        assert len(msg.citations) == 1
        assert msg.citations[0].ticker == "AAPL"

    def test_agent_message_tool_result(self) -> None:
        """Test agent message representing a tool result."""
        msg = AgentMessage(
            role="tool",
            content='{"revenue": 100000000000}',
            tool_use_id="toolu_123456",
        )
        assert msg.role == "tool"
        assert msg.tool_use_id == "toolu_123456"


class TestToolResultModel:
    """Tests for ToolResult model."""

    def test_tool_result_success(self) -> None:
        """Test successful tool result."""
        result = ToolResult(
            tool_name="get_company_info",
            success=True,
            result={"ticker": "AAPL", "name": "Apple Inc."},
            execution_time_ms=150,
        )
        assert result.tool_name == "get_company_info"
        assert result.success is True
        assert result.result["ticker"] == "AAPL"
        assert result.error is None
        assert result.execution_time_ms == 150

    def test_tool_result_failure(self) -> None:
        """Test failed tool result."""
        result = ToolResult(
            tool_name="get_company_info",
            success=False,
            result=None,
            error="Company not found",
            execution_time_ms=50,
        )
        assert result.success is False
        assert result.error == "Company not found"

    def test_tool_result_with_citations(self) -> None:
        """Test tool result with citations."""
        citation = Citation(
            ticker="AAPL",
            form_type="10-K",
            filing_date=date(2024, 10, 31),
            accession_number="0000320193-24-000123",
        )
        result = ToolResult(
            tool_name="get_filing_section",
            success=True,
            result={"content": "Risk factors..."},
            citations=[citation],
            execution_time_ms=300,
        )
        assert len(result.citations) == 1
        assert result.citations[0].ticker == "AAPL"


class TestModelValidation:
    """Tests for model validation edge cases."""

    def test_invalid_date_format(self) -> None:
        """Test that invalid date formats are rejected."""
        with pytest.raises(ValidationError):
            Filing(
                accession_number="0000320193-24-000123",
                form_type="10-K",
                filing_date="not-a-date",  # type: ignore
                company=Company(cik="0000320193", ticker="AAPL", name="Apple Inc."),
            )

    def test_empty_string_validation(self) -> None:
        """Test handling of empty strings."""
        # Empty strings should be allowed for optional fields
        company = Company(
            cik="0000320193",
            ticker="AAPL",
            name="Apple Inc.",
            sic="",  # Empty string
        )
        assert company.sic == ""

    def test_none_vs_missing_field(self) -> None:
        """Test difference between None and missing field."""
        # Both should be treated the same for optional fields
        company1 = Company(cik="0000320193", ticker="AAPL", name="Apple Inc.", sic=None)
        company2 = Company(cik="0000320193", ticker="AAPL", name="Apple Inc.")
        assert company1.sic == company2.sic
