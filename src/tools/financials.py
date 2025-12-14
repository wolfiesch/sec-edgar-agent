"""Financial data extraction tools."""

import logging
from typing import Any

from src.data.edgar_client import get_edgar_client
from src.data.models import Citation
from src.tools.registry import registry

logger = logging.getLogger(__name__)


@registry.register(
    name="get_income_statement",
    description="Get income statement data (revenue, net income, EPS, etc.) from SEC filings. Supports historical years and quarterly data.",
    parameters={
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "Stock ticker symbol (e.g., 'AAPL', 'GOOG', 'MSFT')",
            },
            "periods": {
                "type": "integer",
                "description": "Number of periods to retrieve (used if fiscal_year not specified)",
                "default": 3,
                "minimum": 1,
                "maximum": 10,
            },
            "fiscal_year": {
                "type": "integer",
                "description": "Specific fiscal year to retrieve (e.g., 2011, 2020). If not specified, returns most recent periods.",
            },
            "quarter": {
                "type": "integer",
                "description": "Set to any value (1, 2, or 3) to fetch 10-Q quarterly data instead of 10-K annual data. Returns quarterly periods - check fiscal_period in response.",
                "minimum": 1,
                "maximum": 3,
            },
        },
        "required": ["ticker"],
    },
)
def get_income_statement(
    ticker: str,
    periods: int = 3,
    fiscal_year: int | None = None,
    quarter: int | None = None,
) -> dict[str, Any]:
    """
    Get income statement data.

    Args:
        ticker: Stock ticker symbol.
        periods: Number of periods (years/quarters) to retrieve.
        fiscal_year: Specific fiscal year to retrieve (e.g., 2023).
        quarter: Specific quarter to retrieve (1-3).

    Returns:
        Dictionary containing income statement data.
    """
    client = get_edgar_client()

    try:
        statements = client.get_financials(
            ticker=ticker,
            statement_type="income_statement",
            periods=periods,
            fiscal_year=fiscal_year,
            quarter=quarter,
        )

        if not statements:
            period_desc = f"Q{quarter} " if quarter else ""
            year_desc = f"for {fiscal_year}" if fiscal_year else ""
            return {
                "success": False,
                "error": f"No income statement data found for {ticker} {period_desc}{year_desc}".strip(),
            }

        # Build citations - use 10-Q for quarterly, 10-K for annual
        citations = [
            Citation(
                ticker=ticker.upper(),
                form_type="10-Q" if s.fiscal_period.startswith("Q") else "10-K",
                filing_date=s.period_end,
                section="Financial Statements",
                accession_number="",  # Would need to track this
            )
            for s in statements
        ]

        return {
            "success": True,
            "ticker": ticker.upper(),
            "periods": len(statements),
            "statements": [
                {
                    "fiscal_year": s.fiscal_year,
                    "fiscal_period": s.fiscal_period,
                    "period_end": s.period_end.isoformat(),
                    "currency": s.currency,
                    "data": s.data,
                }
                for s in statements
            ],
            "citations": citations,
        }

    except Exception as e:
        logger.error(f"Failed to get income statement: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@registry.register(
    name="get_balance_sheet",
    description="Get balance sheet data (assets, liabilities, equity) from SEC filings. Supports historical years and quarterly data.",
    parameters={
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "Stock ticker symbol (e.g., 'AAPL', 'GOOG', 'MSFT')",
            },
            "periods": {
                "type": "integer",
                "description": "Number of periods to retrieve (used if fiscal_year not specified)",
                "default": 3,
            },
            "fiscal_year": {
                "type": "integer",
                "description": "Specific fiscal year to retrieve (e.g., 2011, 2020). If not specified, returns most recent periods.",
            },
            "quarter": {
                "type": "integer",
                "description": "Set to any value (1, 2, or 3) to fetch 10-Q quarterly data instead of 10-K annual data. Returns quarterly periods - check fiscal_period in response.",
                "minimum": 1,
                "maximum": 3,
            },
        },
        "required": ["ticker"],
    },
)
def get_balance_sheet(
    ticker: str,
    periods: int = 3,
    fiscal_year: int | None = None,
    quarter: int | None = None,
) -> dict[str, Any]:
    """
    Get balance sheet data.

    Args:
        ticker: Stock ticker symbol.
        periods: Number of periods (years/quarters) to retrieve.
        fiscal_year: Specific fiscal year to retrieve (e.g., 2023).
        quarter: Specific quarter to retrieve (1-3).

    Returns:
        Dictionary containing balance sheet data.
    """
    client = get_edgar_client()

    try:
        statements = client.get_financials(
            ticker=ticker,
            statement_type="balance_sheet",
            periods=periods,
            fiscal_year=fiscal_year,
            quarter=quarter,
        )

        if not statements:
            period_desc = f"Q{quarter} " if quarter else ""
            year_desc = f"for {fiscal_year}" if fiscal_year else ""
            return {
                "success": False,
                "error": f"No balance sheet data found for {ticker} {period_desc}{year_desc}".strip(),
            }

        return {
            "success": True,
            "ticker": ticker.upper(),
            "periods": len(statements),
            "statements": [
                {
                    "fiscal_year": s.fiscal_year,
                    "fiscal_period": s.fiscal_period,
                    "period_end": s.period_end.isoformat(),
                    "currency": s.currency,
                    "data": s.data,
                }
                for s in statements
            ],
        }

    except Exception as e:
        logger.error(f"Failed to get balance sheet: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@registry.register(
    name="get_cash_flow",
    description="Get cash flow statement data from SEC filings. Supports historical years and quarterly data.",
    parameters={
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "Stock ticker symbol (e.g., 'AAPL', 'GOOG', 'MSFT')",
            },
            "periods": {
                "type": "integer",
                "description": "Number of periods to retrieve (used if fiscal_year not specified)",
                "default": 3,
            },
            "fiscal_year": {
                "type": "integer",
                "description": "Specific fiscal year to retrieve (e.g., 2011, 2020). If not specified, returns most recent periods.",
            },
            "quarter": {
                "type": "integer",
                "description": "Set to any value (1, 2, or 3) to fetch 10-Q quarterly data instead of 10-K annual data. Returns quarterly periods - check fiscal_period in response.",
                "minimum": 1,
                "maximum": 3,
            },
        },
        "required": ["ticker"],
    },
)
def get_cash_flow(
    ticker: str,
    periods: int = 3,
    fiscal_year: int | None = None,
    quarter: int | None = None,
) -> dict[str, Any]:
    """
    Get cash flow statement data.

    Args:
        ticker: Stock ticker symbol.
        periods: Number of periods (years/quarters) to retrieve.
        fiscal_year: Specific fiscal year to retrieve (e.g., 2023).
        quarter: Specific quarter to retrieve (1-3).

    Returns:
        Dictionary containing cash flow statement data.
    """
    client = get_edgar_client()

    try:
        statements = client.get_financials(
            ticker=ticker,
            statement_type="cash_flow",
            periods=periods,
            fiscal_year=fiscal_year,
            quarter=quarter,
        )

        if not statements:
            period_desc = f"Q{quarter} " if quarter else ""
            year_desc = f"for {fiscal_year}" if fiscal_year else ""
            return {
                "success": False,
                "error": f"No cash flow data found for {ticker} {period_desc}{year_desc}".strip(),
            }

        return {
            "success": True,
            "ticker": ticker.upper(),
            "periods": len(statements),
            "statements": [
                {
                    "fiscal_year": s.fiscal_year,
                    "fiscal_period": s.fiscal_period,
                    "period_end": s.period_end.isoformat(),
                    "currency": s.currency,
                    "data": s.data,
                }
                for s in statements
            ],
        }

    except Exception as e:
        logger.error(f"Failed to get cash flow: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@registry.register(
    name="get_insider_trades",
    description="Get recent insider trading activity (Form 4) for a company",
    parameters={
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "Stock ticker symbol",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of transactions to return",
                "default": 20,
            },
        },
        "required": ["ticker"],
    },
)
def get_insider_trades(
    ticker: str,
    limit: int = 20,
) -> dict[str, Any]:
    """
    Get insider trading transactions.

    Args:
        ticker: Stock ticker symbol.
        limit: Maximum number of transactions to return (default: 20).

    Returns:
        Dictionary containing a summary of insider transactions.
    """
    client = get_edgar_client()

    try:
        transactions = client.get_insider_transactions(ticker, limit)

        if not transactions:
            return {
                "success": True,
                "ticker": ticker.upper(),
                "message": "No recent insider transactions found",
                "transactions": [],
            }

        # Summarize by insider
        by_insider: dict[str, dict[str, Any]] = {}
        for txn in transactions:
            name = txn.insider_name
            if name not in by_insider:
                by_insider[name] = {
                    "name": name,
                    "title": txn.insider_title,
                    "total_bought": 0,
                    "total_sold": 0,
                    "transactions": [],
                }

            if txn.transaction_type == "P":
                by_insider[name]["total_bought"] += txn.shares
            elif txn.transaction_type == "S":
                by_insider[name]["total_sold"] += txn.shares

            by_insider[name]["transactions"].append({
                "date": txn.transaction_date.isoformat(),
                "type": "Buy" if txn.transaction_type == "P" else "Sell" if txn.transaction_type == "S" else txn.transaction_type,
                "shares": txn.shares,
                "price": txn.price_per_share,
                "value": txn.total_value,
            })

        return {
            "success": True,
            "ticker": ticker.upper(),
            "transaction_count": len(transactions),
            "by_insider": list(by_insider.values()),
        }

    except Exception as e:
        logger.error(f"Failed to get insider trades: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@registry.register(
    name="compare_financials",
    description="Compare a financial metric across multiple companies",
    parameters={
        "type": "object",
        "properties": {
            "tickers": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of ticker symbols to compare",
                "minItems": 2,
                "maxItems": 5,
            },
            "metric": {
                "type": "string",
                "description": "Financial metric to compare",
                "enum": ["revenue", "net_income", "total_assets", "total_debt", "cash"],
            },
        },
        "required": ["tickers", "metric"],
    },
)
def compare_financials(
    tickers: list[str],
    metric: str,
) -> dict[str, Any]:
    """
    Compare a metric across companies.

    Args:
        tickers: List of stock ticker symbols to compare.
        metric: Financial metric to compare (e.g., 'revenue', 'net_income').

    Returns:
        Dictionary containing comparison results for the specified metric.
    """
    client = get_edgar_client()

    results = []
    for ticker in tickers:
        try:
            company = client.get_company(ticker)

            # Get latest financials
            if metric in ["revenue", "net_income"]:
                statements = client.get_financials(ticker, "income_statement", 1)
            else:
                statements = client.get_financials(ticker, "balance_sheet", 1)

            if statements and statements[0].data:
                value = statements[0].data.get(metric)
                results.append({
                    "ticker": ticker.upper(),
                    "company": company.name,
                    "metric": metric,
                    "value": value,
                    "fiscal_year": statements[0].fiscal_year,
                })
            else:
                results.append({
                    "ticker": ticker.upper(),
                    "company": company.name,
                    "metric": metric,
                    "value": None,
                    "error": "Data not available",
                })

        except Exception as e:
            results.append({
                "ticker": ticker.upper(),
                "error": str(e),
            })

    # Sort by value (descending) where available
    results.sort(
        key=lambda x: x.get("value") or 0,
        reverse=True,
    )

    return {
        "success": True,
        "metric": metric,
        "companies": results,
    }
