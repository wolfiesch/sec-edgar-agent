"""Endpoints for multi-company comparison."""
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.data.edgar_client import get_edgar_client

logger = logging.getLogger(__name__)
router = APIRouter()


class CompareRequest(BaseModel):
    """Request to compare multiple companies."""
    tickers: list[str] = Field(..., min_length=2, max_length=5, description="List of ticker symbols")
    metrics: list[str] = Field(
        default=["revenue", "net_income", "eps"],
        description="Metrics to compare"
    )
    years: int = Field(default=3, ge=1, le=5, description="Number of years of historical data")


class MetricValue(BaseModel):
    """Single metric value with year."""
    year: int
    value: float | None
    yoy_change: float | None = None


class CompanyData(BaseModel):
    """Financial data for a single company."""
    ticker: str
    name: str | None = None
    metrics: dict[str, list[MetricValue]]
    error: str | None = None


class CompareResponse(BaseModel):
    """Response containing comparison data."""
    companies: list[CompanyData]
    metrics: list[str]
    years: int
    generated_at: str


# Metric to statement type mapping
INCOME_METRICS = {"revenue", "net_income", "gross_profit", "operating_income", "gross_margin", "operating_margin", "eps"}
BALANCE_METRICS = {"total_assets", "total_debt", "cash", "total_liabilities", "stockholders_equity"}


def get_metric_value(data: dict, metric: str) -> float | None:
    """Extract metric value from statement data with various field name mappings."""
    # Direct match
    if metric in data:
        return data[metric]

    # Common field name mappings
    mappings = {
        "revenue": ["revenue", "total_revenue", "revenues", "net_revenue", "net_revenues", "total_revenues"],
        "net_income": ["net_income", "net_income_loss", "net_earnings"],
        "gross_profit": ["gross_profit", "gross_margin_total"],
        "operating_income": ["operating_income", "income_from_operations", "operating_income_loss"],
        "total_assets": ["total_assets", "assets"],
        "total_debt": ["total_debt", "long_term_debt", "debt_current_and_long_term"],
        "cash": ["cash_and_cash_equivalents", "cash", "cash_and_equivalents"],
        "total_liabilities": ["total_liabilities", "liabilities"],
        "stockholders_equity": ["stockholders_equity", "total_equity", "total_stockholders_equity"],
        "eps": ["eps", "earnings_per_share", "basic_eps", "diluted_eps"],
    }

    for field_name in mappings.get(metric, []):
        if field_name in data:
            return data[field_name]

    return None


def calculate_derived_metrics(data: dict, metric: str) -> float | None:
    """Calculate derived metrics like margins."""
    if metric == "gross_margin":
        revenue = get_metric_value(data, "revenue")
        gross_profit = get_metric_value(data, "gross_profit")
        if revenue and gross_profit and revenue != 0:
            return (gross_profit / revenue) * 100

    if metric == "operating_margin":
        revenue = get_metric_value(data, "revenue")
        operating_income = get_metric_value(data, "operating_income")
        if revenue and operating_income and revenue != 0:
            return (operating_income / revenue) * 100

    return None


@router.post("", response_model=CompareResponse)
async def compare_companies(request: CompareRequest):
    """
    Compare multiple companies across financial metrics.

    Returns structured data suitable for side-by-side comparison tables and charts.
    """
    client = get_edgar_client()
    companies_data: list[CompanyData] = []

    for ticker in request.tickers:
        try:
            # Get company info
            company = client.get_company(ticker)
            company_name = company.name if company else ticker.upper()

            # Get financial statements
            income_statements = client.get_financials(ticker, "income_statement", request.years)
            balance_sheets = client.get_financials(ticker, "balance_sheet", request.years)

            # Build metrics data
            metrics_data: dict[str, list[MetricValue]] = {}

            for metric in request.metrics:
                metric_values: list[MetricValue] = []

                # Determine which statements to use
                if metric in INCOME_METRICS:
                    statements = income_statements or []
                elif metric in BALANCE_METRICS:
                    statements = balance_sheets or []
                else:
                    # Try both
                    statements = (income_statements or []) + (balance_sheets or [])

                for stmt in statements:
                    if not stmt or not stmt.data:
                        continue

                    # Try to get value
                    value = get_metric_value(stmt.data, metric)

                    # Try derived metrics if direct not found
                    if value is None and metric in ["gross_margin", "operating_margin"]:
                        value = calculate_derived_metrics(stmt.data, metric)

                    metric_values.append(MetricValue(
                        year=stmt.fiscal_year,
                        value=value,
                        yoy_change=None
                    ))

                # Sort by year (newest first)
                metric_values.sort(key=lambda x: x.year, reverse=True)

                # Calculate YoY changes
                for i in range(len(metric_values) - 1):
                    curr = metric_values[i].value
                    prev = metric_values[i + 1].value
                    if curr is not None and prev is not None and prev != 0:
                        metric_values[i].yoy_change = ((curr - prev) / abs(prev)) * 100

                metrics_data[metric] = metric_values

            companies_data.append(CompanyData(
                ticker=ticker.upper(),
                name=company_name,
                metrics=metrics_data,
            ))

        except Exception as e:
            logger.warning(f"Failed to get data for {ticker}: {e}")
            companies_data.append(CompanyData(
                ticker=ticker.upper(),
                name=None,
                metrics={m: [] for m in request.metrics},
                error=str(e),
            ))

    return CompareResponse(
        companies=companies_data,
        metrics=request.metrics,
        years=request.years,
        generated_at=datetime.utcnow().isoformat() + "Z",
    )
