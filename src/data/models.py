"""Pydantic models for SEC EDGAR data structures."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class Company(BaseModel):
    """Represents a company with SEC filings."""

    cik: str = Field(description="Central Index Key (SEC identifier)")
    ticker: str = Field(description="Stock ticker symbol")
    name: str = Field(description="Company name")
    sic: str | None = Field(default=None, description="Standard Industrial Classification code")
    sic_description: str | None = Field(default=None, description="SIC industry description")
    exchange: str | None = Field(default=None, description="Stock exchange")


class Filing(BaseModel):
    """Represents an SEC filing."""

    accession_number: str = Field(description="Unique filing identifier")
    form_type: str = Field(description="Form type (10-K, 10-Q, 8-K, etc.)")
    filing_date: date = Field(description="Date filed with SEC")
    report_date: date | None = Field(default=None, description="Period end date")
    company: Company = Field(description="Company that filed")
    primary_document: str | None = Field(default=None, description="Primary document filename")
    url: str | None = Field(default=None, description="URL to filing on SEC EDGAR")


class FinancialStatement(BaseModel):
    """Represents extracted financial statement data."""

    statement_type: str = Field(description="balance_sheet, income_statement, or cash_flow")
    period_end: date = Field(description="Period end date")
    fiscal_year: int = Field(description="Fiscal year")
    fiscal_period: str = Field(description="FY, Q1, Q2, Q3, Q4")
    currency: str = Field(default="USD", description="Currency code")
    data: dict[str, Any] = Field(description="Financial line items and values")


class FilingSection(BaseModel):
    """Represents a section extracted from a filing."""

    filing_accession: str = Field(description="Parent filing accession number")
    section_name: str = Field(description="Section name (e.g., 'Risk Factors')")
    section_number: str | None = Field(default=None, description="Item number if applicable")
    content: str = Field(description="Section text content")
    page_start: int | None = Field(default=None, description="Starting page number")
    page_end: int | None = Field(default=None, description="Ending page number")


class InsiderTransaction(BaseModel):
    """Represents an insider transaction from Form 4."""

    accession_number: str = Field(description="Filing accession number")
    filing_date: date = Field(description="Date filed")
    company: Company = Field(description="Company")
    insider_name: str = Field(description="Name of insider")
    insider_title: str | None = Field(default=None, description="Title/position")
    transaction_date: date = Field(description="Date of transaction")
    transaction_type: str = Field(description="P (purchase), S (sale), etc.")
    shares: float = Field(description="Number of shares")
    price_per_share: float | None = Field(default=None, description="Price per share")
    total_value: float | None = Field(default=None, description="Total transaction value")
    shares_owned_after: float | None = Field(default=None, description="Shares owned after transaction")


class Citation(BaseModel):
    """Represents a citation to a source filing."""

    ticker: str = Field(description="Company ticker")
    form_type: str = Field(description="Form type")
    filing_date: date = Field(description="Filing date")
    section: str | None = Field(default=None, description="Section name")
    page: int | None = Field(default=None, description="Page number")
    accession_number: str = Field(description="Filing accession number")

    def __str__(self) -> str:
        """Format citation as string."""
        parts = [self.ticker, self.form_type, str(self.filing_date.year)]
        if self.section:
            parts.append(self.section)
        if self.page:
            parts.append(f"p.{self.page}")
        return f"[{', '.join(parts)}]"


class AgentMessage(BaseModel):
    """Message in agent conversation."""

    role: str = Field(description="user, assistant, or tool")
    content: str = Field(description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now)
    tool_use_id: str | None = Field(default=None, description="Tool use ID if tool result")
    citations: list[Citation] = Field(default_factory=list, description="Source citations")


class ToolResult(BaseModel):
    """Result from a tool execution."""

    tool_name: str = Field(description="Name of the tool")
    success: bool = Field(description="Whether execution succeeded")
    result: Any = Field(description="Tool result data")
    error: str | None = Field(default=None, description="Error message if failed")
    citations: list[Citation] = Field(default_factory=list, description="Source citations")
    execution_time_ms: int = Field(description="Execution time in milliseconds")
