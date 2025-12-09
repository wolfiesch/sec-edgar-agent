"""Advanced analysis tools for SEC filings."""

import logging
from datetime import date
from typing import Any

from src.data.edgar_client import get_edgar_client
from src.data.models import Citation
from src.tools.registry import registry

logger = logging.getLogger(__name__)


@registry.register(
    name="analyze_historical_trends",
    description="Analyze year-over-year changes in financial metrics for a company. Shows trends, growth rates, and significant changes.",
    parameters={
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "Stock ticker symbol",
            },
            "metric": {
                "type": "string",
                "description": "Financial metric to analyze",
                "enum": ["revenue", "net_income", "total_assets", "total_debt", "operating_income", "gross_profit"],
            },
            "years": {
                "type": "integer",
                "description": "Number of years to analyze",
                "default": 5,
                "minimum": 2,
                "maximum": 10,
            },
        },
        "required": ["ticker", "metric"],
    },
)
def analyze_historical_trends(
    ticker: str,
    metric: str,
    years: int = 5,
) -> dict[str, Any]:
    """Analyze historical trends for a financial metric."""
    client = get_edgar_client()

    try:
        # Determine which statement type to use
        if metric in ["revenue", "net_income", "operating_income", "gross_profit"]:
            statement_type = "income_statement"
        else:
            statement_type = "balance_sheet"

        statements = client.get_financials(
            ticker=ticker,
            statement_type=statement_type,
            periods=years,
        )

        if not statements:
            return {
                "success": False,
                "error": f"No financial data found for {ticker}",
            }

        # Extract metric values by year
        data_points = []
        for stmt in statements:
            value = stmt.data.get(metric)
            if value is not None:
                data_points.append({
                    "year": stmt.fiscal_year,
                    "period_end": stmt.period_end.isoformat(),
                    "value": float(value),
                })

        if len(data_points) < 2:
            return {
                "success": False,
                "error": f"Insufficient data points for trend analysis (need at least 2, got {len(data_points)})",
            }

        # Sort by year (oldest first)
        data_points.sort(key=lambda x: x["year"])

        # Calculate YoY changes
        for i in range(1, len(data_points)):
            prev = data_points[i - 1]["value"]
            curr = data_points[i]["value"]
            if prev != 0:
                change_pct = ((curr - prev) / abs(prev)) * 100
            else:
                change_pct = None
            data_points[i]["yoy_change"] = curr - prev
            data_points[i]["yoy_change_pct"] = change_pct

        # Calculate CAGR (Compound Annual Growth Rate)
        first_value = data_points[0]["value"]
        last_value = data_points[-1]["value"]
        num_years = len(data_points) - 1

        if first_value > 0 and last_value > 0 and num_years > 0:
            cagr = ((last_value / first_value) ** (1 / num_years) - 1) * 100
        else:
            cagr = None

        # Determine trend direction
        positive_changes = sum(1 for dp in data_points[1:] if dp.get("yoy_change", 0) > 0)
        negative_changes = sum(1 for dp in data_points[1:] if dp.get("yoy_change", 0) < 0)

        if positive_changes > negative_changes * 2:
            trend = "strong_growth"
        elif positive_changes > negative_changes:
            trend = "moderate_growth"
        elif negative_changes > positive_changes * 2:
            trend = "strong_decline"
        elif negative_changes > positive_changes:
            trend = "moderate_decline"
        else:
            trend = "stable"

        # Generate narrative
        narrative = _generate_trend_narrative(
            ticker, metric, data_points, trend, cagr
        )

        return {
            "success": True,
            "ticker": ticker.upper(),
            "metric": metric,
            "period": f"{data_points[0]['year']}-{data_points[-1]['year']}",
            "data_points": data_points,
            "summary": {
                "trend": trend,
                "cagr": round(cagr, 2) if cagr else None,
                "total_change": last_value - first_value,
                "total_change_pct": ((last_value - first_value) / abs(first_value) * 100) if first_value != 0 else None,
            },
            "narrative": narrative,
        }

    except Exception as e:
        logger.error(f"Historical analysis failed: {e}")
        return {
            "success": False,
            "error": str(e),
        }


def _generate_trend_narrative(
    ticker: str,
    metric: str,
    data_points: list[dict],
    trend: str,
    cagr: float | None,
) -> str:
    """Generate a human-readable narrative for the trend."""
    metric_names = {
        "revenue": "Revenue",
        "net_income": "Net Income",
        "total_assets": "Total Assets",
        "total_debt": "Total Debt",
        "operating_income": "Operating Income",
        "gross_profit": "Gross Profit",
    }

    metric_name = metric_names.get(metric, metric.replace("_", " ").title())
    first = data_points[0]
    last = data_points[-1]

    # Format values
    def fmt(val: float) -> str:
        if abs(val) >= 1e9:
            return f"${val/1e9:.1f}B"
        elif abs(val) >= 1e6:
            return f"${val/1e6:.1f}M"
        else:
            return f"${val:,.0f}"

    trend_desc = {
        "strong_growth": "showed strong consistent growth",
        "moderate_growth": "showed moderate growth",
        "strong_decline": "experienced significant decline",
        "moderate_decline": "showed moderate decline",
        "stable": "remained relatively stable",
    }

    narrative = f"{ticker.upper()}'s {metric_name} {trend_desc.get(trend, 'changed')} "
    narrative += f"from {fmt(first['value'])} in {first['year']} to {fmt(last['value'])} in {last['year']}. "

    if cagr is not None:
        narrative += f"This represents a CAGR of {cagr:.1f}%. "

    # Note significant years
    max_change = max(data_points[1:], key=lambda x: abs(x.get("yoy_change_pct", 0) or 0), default=None)
    if max_change and max_change.get("yoy_change_pct"):
        pct = max_change["yoy_change_pct"]
        direction = "increased" if pct > 0 else "decreased"
        narrative += f"The most significant change was in {max_change['year']}, when {metric_name} {direction} by {abs(pct):.1f}%."

    return narrative


@registry.register(
    name="compare_companies",
    description="Compare multiple companies across several financial metrics. Useful for peer analysis and sector comparisons.",
    parameters={
        "type": "object",
        "properties": {
            "tickers": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of ticker symbols to compare (2-5 companies)",
                "minItems": 2,
                "maxItems": 5,
            },
            "metrics": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["revenue", "net_income", "total_assets", "total_debt", "gross_profit"],
                },
                "description": "Metrics to compare",
                "default": ["revenue", "net_income"],
            },
        },
        "required": ["tickers"],
    },
)
def compare_companies(
    tickers: list[str],
    metrics: list[str] | None = None,
) -> dict[str, Any]:
    """Compare multiple companies across metrics."""
    if metrics is None:
        metrics = ["revenue", "net_income"]

    client = get_edgar_client()
    results = []

    for ticker in tickers:
        try:
            company = client.get_company(ticker)

            # Get latest financials
            income = client.get_financials(ticker, "income_statement", 1)
            balance = client.get_financials(ticker, "balance_sheet", 1)

            company_data = {
                "ticker": ticker.upper(),
                "name": company.name,
                "metrics": {},
            }

            for metric in metrics:
                value = None
                if metric in ["revenue", "net_income", "gross_profit", "operating_income"]:
                    if income and income[0].data:
                        value = income[0].data.get(metric)
                else:
                    if balance and balance[0].data:
                        value = balance[0].data.get(metric)

                company_data["metrics"][metric] = value

            results.append(company_data)

        except Exception as e:
            logger.warning(f"Failed to get data for {ticker}: {e}")
            results.append({
                "ticker": ticker.upper(),
                "error": str(e),
            })

    # Calculate rankings for each metric
    rankings = {}
    for metric in metrics:
        values = [
            (r["ticker"], r["metrics"].get(metric))
            for r in results
            if "metrics" in r and r["metrics"].get(metric) is not None
        ]
        values.sort(key=lambda x: x[1] or 0, reverse=True)
        rankings[metric] = [v[0] for v in values]

    return {
        "success": True,
        "companies": results,
        "metrics_compared": metrics,
        "rankings": rankings,
    }


@registry.register(
    name="detect_risk_changes",
    description="Compare risk factors between two filing periods to identify new, removed, or modified risks.",
    parameters={
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "Stock ticker symbol",
            },
            "year1": {
                "type": "integer",
                "description": "First year to compare (earlier)",
            },
            "year2": {
                "type": "integer",
                "description": "Second year to compare (later)",
            },
        },
        "required": ["ticker", "year1", "year2"],
    },
)
def detect_risk_changes(
    ticker: str,
    year1: int,
    year2: int,
) -> dict[str, Any]:
    """Compare risk factors between two years."""
    client = get_edgar_client()

    try:
        # Get filings for both years
        filings = client.get_filings(
            ticker=ticker,
            form_type="10-K",
            limit=10,
            start_date=date(year1, 1, 1),
            end_date=date(year2, 12, 31),
        )

        # Find filings closest to each year
        filing1 = None
        filing2 = None

        for f in filings:
            if f.filing_date.year == year1 or (f.filing_date.year == year1 + 1 and f.filing_date.month <= 3):
                if filing1 is None or f.filing_date > filing1.filing_date:
                    filing1 = f
            if f.filing_date.year == year2 or (f.filing_date.year == year2 + 1 and f.filing_date.month <= 3):
                if filing2 is None or f.filing_date > filing2.filing_date:
                    filing2 = f

        if not filing1 or not filing2:
            return {
                "success": False,
                "error": f"Could not find 10-K filings for years {year1} and {year2}",
            }

        # [*TO-DO*] - Extract and compare risk factor sections
        # This requires parsing the full filing text and doing semantic comparison
        # For now, return filing metadata

        return {
            "success": True,
            "ticker": ticker.upper(),
            "comparison": {
                "year1": {
                    "fiscal_year": year1,
                    "filing_date": filing1.filing_date.isoformat(),
                    "accession": filing1.accession_number,
                },
                "year2": {
                    "fiscal_year": year2,
                    "filing_date": filing2.filing_date.isoformat(),
                    "accession": filing2.accession_number,
                },
            },
            "note": "Risk factor comparison requires manual review of the filings above. Use get_filing_section to extract Risk Factors from each.",
        }

    except Exception as e:
        logger.error(f"Risk change detection failed: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@registry.register(
    name="get_sector_peers",
    description="Find peer companies in the same sector/industry based on SIC code.",
    parameters={
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "Stock ticker to find peers for",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of peers to return",
                "default": 5,
            },
        },
        "required": ["ticker"],
    },
)
def get_sector_peers(
    ticker: str,
    limit: int = 5,
) -> dict[str, Any]:
    """Find peer companies in the same sector."""
    client = get_edgar_client()

    try:
        company = client.get_company(ticker)

        # [*TO-DO*] - Implement proper peer lookup using SIC codes
        # For now, return common peer groups
        sector_peers = {
            "AAPL": ["MSFT", "GOOGL", "META", "AMZN"],
            "MSFT": ["AAPL", "GOOGL", "ORCL", "CRM"],
            "GOOGL": ["META", "MSFT", "AMZN", "NFLX"],
            "AMZN": ["WMT", "TGT", "COST", "EBAY"],
            "TSLA": ["F", "GM", "RIVN", "LCID"],
            "JPM": ["BAC", "WFC", "C", "GS"],
            "JNJ": ["PFE", "MRK", "ABBV", "UNH"],
        }

        peers = sector_peers.get(ticker.upper(), [])[:limit]

        return {
            "success": True,
            "ticker": ticker.upper(),
            "company": company.name,
            "sic": company.sic,
            "peers": peers,
            "note": "Peer list is approximate. For precise sector analysis, verify SIC codes match.",
        }

    except Exception as e:
        logger.error(f"Peer lookup failed: {e}")
        return {
            "success": False,
            "error": str(e),
        }
