"""Search tools for SEC filings."""

from datetime import date
from typing import Any

from src.data.edgar_client import get_edgar_client
from src.data.models import Citation
from src.tools.registry import registry


@registry.register(
    name="get_company_info",
    description="Get basic information about a company including CIK, name, industry, and exchange",
    parameters={
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "Stock ticker symbol (e.g., 'AAPL', 'MSFT')",
            },
        },
        "required": ["ticker"],
    },
)
def get_company_info(ticker: str) -> dict[str, Any]:
    """Get company information by ticker."""
    client = get_edgar_client()
    company = client.get_company(ticker)

    return {
        "cik": company.cik,
        "ticker": company.ticker,
        "name": company.name,
        "sic": company.sic,
        "sic_description": company.sic_description,
        "exchange": company.exchange,
    }


@registry.register(
    name="search_filings",
    description="Search for SEC filings by company ticker and form type. Returns list of filings with dates and accession numbers.",
    parameters={
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "Stock ticker symbol (e.g., 'AAPL')",
            },
            "form_type": {
                "type": "string",
                "description": "SEC form type: '10-K' (annual), '10-Q' (quarterly), '8-K' (events), '4' (insider)",
                "enum": ["10-K", "10-Q", "8-K", "4", "DEF 14A", "S-1", "13F-HR"],
                "default": "10-K",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of filings to return",
                "default": 5,
                "minimum": 1,
                "maximum": 20,
            },
            "start_year": {
                "type": "integer",
                "description": "Filter filings from this year onwards",
            },
            "end_year": {
                "type": "integer",
                "description": "Filter filings up to this year",
            },
        },
        "required": ["ticker"],
    },
)
def search_filings(
    ticker: str,
    form_type: str = "10-K",
    limit: int = 5,
    start_year: int | None = None,
    end_year: int | None = None,
) -> dict[str, Any]:
    """Search for SEC filings."""
    client = get_edgar_client()

    start_date = date(start_year, 1, 1) if start_year else None
    end_date = date(end_year, 12, 31) if end_year else None

    filings = client.get_filings(
        ticker=ticker,
        form_type=form_type,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
    )

    # Build citations for each filing
    citations = [
        Citation(
            ticker=f.company.ticker,
            form_type=f.form_type,
            filing_date=f.filing_date,
            accession_number=f.accession_number,
        )
        for f in filings
    ]

    return {
        "company": filings[0].company.ticker if filings else ticker.upper(),
        "form_type": form_type,
        "count": len(filings),
        "filings": [
            {
                "accession_number": f.accession_number,
                "form_type": f.form_type,
                "filing_date": f.filing_date.isoformat(),
                "report_date": f.report_date.isoformat() if f.report_date else None,
                "url": f.url,
            }
            for f in filings
        ],
        "citations": citations,
    }


@registry.register(
    name="list_available_forms",
    description="List all available SEC form types and their descriptions",
    parameters={
        "type": "object",
        "properties": {},
    },
)
def list_available_forms() -> dict[str, Any]:
    """List available SEC form types."""
    return {
        "forms": [
            {
                "form": "10-K",
                "description": "Annual report with comprehensive business overview and audited financials",
            },
            {
                "form": "10-Q",
                "description": "Quarterly report with unaudited financials",
            },
            {
                "form": "8-K",
                "description": "Current report for material events (earnings, acquisitions, leadership changes)",
            },
            {
                "form": "4",
                "description": "Insider trading - stock purchases/sales by executives and directors",
            },
            {
                "form": "DEF 14A",
                "description": "Proxy statement with executive compensation and board info",
            },
            {
                "form": "S-1",
                "description": "IPO registration statement",
            },
            {
                "form": "13F-HR",
                "description": "Quarterly holdings report from institutional investors",
            },
            {
                "form": "SC 13D",
                "description": "Beneficial ownership report (activist investors)",
            },
        ]
    }
