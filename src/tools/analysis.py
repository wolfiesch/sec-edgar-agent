"""Advanced analysis tools for SEC filings."""

import logging
from datetime import date
from typing import Any

from src.data.edgar_client import get_edgar_client
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
        data_points.sort(key=lambda x: int(str(x.get("year", 0))))

        # Calculate YoY changes
        for i in range(1, len(data_points)):
            prev_val = data_points[i - 1].get("value", 0)
            curr_val = data_points[i].get("value", 0)
            
        try:
            prev_float = float(str(prev_val)) if prev_val is not None else 0.0
            curr_float = float(str(curr_val)) if curr_val is not None else 0.0
            
            prev = prev_float
            curr = curr_float
        except (ValueError, TypeError):
            prev = 0.0
            curr = 0.0
                
            if prev != 0:
                change_pct: float | None = ((curr - prev) / abs(prev)) * 100
            else:
                change_pct = None
            data_points[i]["yoy_change"] = curr - prev
            data_points[i]["yoy_change_pct"] = change_pct

        # Calculate CAGR (Compound Annual Growth Rate)
        first_val = data_points[0].get("value", 0)
        last_val = data_points[-1].get("value", 0)
        
        try:
            first_val = float(str(first_val)) if first_val is not None else 0.0
            last_val = float(str(last_val)) if last_val is not None else 0.0
        except (ValueError, TypeError):
            first_val = 0.0
            last_val = 0.0
            
        num_years = len(data_points) - 1

        if first_val > 0 and last_val > 0 and num_years > 0:
            cagr: float | None = ((last_val / first_val) ** (1 / num_years) - 1) * 100
        else:
            cagr = None

        # Determine trend direction
        # Ensure values are cast to float for comparison
        yoy_changes = []
        for dp in data_points[1:]:
            val = dp.get("yoy_change", 0)
            if val is None:
                val = 0
            yoy_changes.append(float(str(val)))

        positive_changes = sum(1 for x in yoy_changes if x > 0)
        negative_changes = sum(1 for x in yoy_changes if x < 0)

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
            "period": f"{data_points[0].get('year')}-{data_points[-1].get('year')}",
            "data_points": data_points,
            "summary": {
                "trend": trend,
                "cagr": round(cagr, 2) if cagr else None,
                "total_change": last_val - first_val,
                "total_change_pct": ((last_val - first_val) / abs(first_val) * 100) if first_val != 0 else None,
            },
            "narrative": narrative,
            "error": None
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
        """Format numeric values with currency units for readability."""
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

            company_data: dict[str, Any] = {
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


def _extract_risk_section(ticker: str, accession_number: str) -> str | None:
    """
    Extract risk factors section from a filing.

    Returns the text content of Item 1A (Risk Factors), or None if not found.
    """
    client = get_edgar_client()
    filing = client.get_filing_by_accession(ticker, accession_number)

    if not filing:
        return None

    try:
        # Try to get the TenK object for section extraction
        obj = filing.obj()

        content = None
        # Try edgartools section accessor
        if hasattr(obj, "item_1a"):
            content = obj.item_1a
        elif hasattr(obj, "get_section"):
            content = obj.get_section("Item 1A")

        if content is None:
            # Fallback: search in text
            text = filing.text() if hasattr(filing, "text") else str(filing)
            item_upper = "ITEM 1A"
            start_idx = text.upper().find(item_upper)
            if start_idx != -1:
                # Find next item (Item 1B, Item 2, etc.)
                end_idx = len(text)
                for next_item in ["ITEM 1B", "ITEM 2", "ITEM 3"]:
                    next_idx = text.upper().find(next_item, start_idx + 100)
                    if next_idx != -1 and next_idx < end_idx:
                        end_idx = next_idx
                content = text[start_idx:end_idx]

        return str(content) if content else None

    except Exception as e:
        logger.warning(f"Failed to extract risk section: {e}")
        return None


def _extract_risk_paragraphs(text: str) -> list[str]:
    """
    Split risk factor text into individual risk paragraphs.

    Risk factors typically have headers/titles followed by descriptive paragraphs.
    """
    import re

    if not text:
        return []

    # Clean up the text
    text = re.sub(r'\s+', ' ', text)

    # Try to split by common risk header patterns
    # Patterns like "Risk Title" followed by description, or bullet points
    paragraphs = []

    # Split by double newlines or numbered/bulleted items
    # Also look for bold/capitalized headers
    sections = re.split(r'\n\s*\n|\n(?=[•\-\*]|\d+\.)', text)

    for section in sections:
        section = section.strip()
        if len(section) > 50:  # Minimum meaningful risk description
            # Truncate very long sections
            if len(section) > 2000:
                section = section[:2000] + "..."
            paragraphs.append(section)

    return paragraphs[:50]  # Limit to 50 risk factors


def _compare_risk_texts(risks1: list[str], risks2: list[str]) -> dict[str, Any]:
    """
    Compare two lists of risk factor texts to identify changes.

    Uses simple text similarity to find new, removed, and modified risks.
    """
    from difflib import SequenceMatcher

    def similarity(a: str, b: str) -> float:
        """Calculate similarity ratio between two strings."""
        # Normalize for comparison
        a_norm = a.lower()[:500]
        b_norm = b.lower()[:500]
        return SequenceMatcher(None, a_norm, b_norm).ratio()

    # Match risks between years
    matched_pairs: list[tuple[int, int, float]] = []  # (idx1, idx2, similarity)
    used_idx1: set[int] = set()
    used_idx2: set[int] = set()

    # Find best matches
    for i, r1 in enumerate(risks1):
        best_match = -1
        best_sim = 0.0

        for j, r2 in enumerate(risks2):
            if j in used_idx2:
                continue
            sim = similarity(r1, r2)
            if sim > best_sim and sim > 0.5:  # Threshold for matching
                best_sim = sim
                best_match = j

        if best_match >= 0:
            matched_pairs.append((i, best_match, best_sim))
            used_idx1.add(i)
            used_idx2.add(best_match)

    # Categorize changes
    new_risks = [risks2[j] for j in range(len(risks2)) if j not in used_idx2]
    removed_risks = [risks1[i] for i in range(len(risks1)) if i not in used_idx1]

    # Find significantly modified risks (matched but < 0.8 similarity)
    modified_risks = []
    unchanged_risks = []

    for i, j, sim in matched_pairs:
        if sim < 0.8:
            modified_risks.append({
                "similarity": round(sim, 2),
                "before": risks1[i][:500] + ("..." if len(risks1[i]) > 500 else ""),
                "after": risks2[j][:500] + ("..." if len(risks2[j]) > 500 else ""),
            })
        else:
            unchanged_risks.append(risks1[i][:200] + ("..." if len(risks1[i]) > 200 else ""))

    return {
        "new_risks": [r[:500] + ("..." if len(r) > 500 else "") for r in new_risks[:10]],
        "removed_risks": [r[:500] + ("..." if len(r) > 500 else "") for r in removed_risks[:10]],
        "modified_risks": modified_risks[:10],
        "unchanged_count": len(unchanged_risks),
        "summary": {
            "total_year1": len(risks1),
            "total_year2": len(risks2),
            "new_count": len(new_risks),
            "removed_count": len(removed_risks),
            "modified_count": len(modified_risks),
        },
    }


@registry.register(
    name="detect_risk_changes",
    description="Compare risk factors between two filing periods to identify new, removed, or modified risks. Extracts Item 1A (Risk Factors) from 10-K filings and performs text comparison.",
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
        # 10-K is typically filed in Q1 of the following year (for fiscal year ending Dec 31)
        filing1 = None
        filing2 = None

        for f in filings:
            # Filing for fiscal year X is usually filed in early year X+1
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

        # Extract risk factor sections
        logger.info(f"Extracting risk factors for {ticker} - {year1} vs {year2}")

        risks_text1 = _extract_risk_section(ticker, filing1.accession_number)
        risks_text2 = _extract_risk_section(ticker, filing2.accession_number)

        if not risks_text1 or not risks_text2:
            return {
                "success": True,
                "ticker": ticker.upper(),
                "comparison": {
                    "year1": {
                        "fiscal_year": year1,
                        "filing_date": filing1.filing_date.isoformat(),
                        "accession": filing1.accession_number,
                        "risk_section_found": bool(risks_text1),
                    },
                    "year2": {
                        "fiscal_year": year2,
                        "filing_date": filing2.filing_date.isoformat(),
                        "accession": filing2.accession_number,
                        "risk_section_found": bool(risks_text2),
                    },
                },
                "note": "Could not extract risk factor sections. Use get_filing_section to manually review.",
            }

        # Parse into individual risk paragraphs
        risks1 = _extract_risk_paragraphs(risks_text1)
        risks2 = _extract_risk_paragraphs(risks_text2)

        # Compare the risk factors
        comparison = _compare_risk_texts(risks1, risks2)

        # Generate narrative summary
        summary = comparison["summary"]
        narrative = f"{ticker.upper()}'s risk disclosure evolved from {year1} to {year2}. "

        if summary["new_count"] > 0:
            narrative += f"Added {summary['new_count']} new risk factor(s). "
        if summary["removed_count"] > 0:
            narrative += f"Removed {summary['removed_count']} risk factor(s). "
        if summary["modified_count"] > 0:
            narrative += f"{summary['modified_count']} risk factor(s) were significantly modified. "
        if summary["new_count"] == 0 and summary["removed_count"] == 0 and summary["modified_count"] == 0:
            narrative += "Risk factors remained largely unchanged."

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
            "changes": comparison,
            "narrative": narrative,
        }

    except Exception as e:
        logger.error(f"Risk change detection failed: {e}")
        return {
            "success": False,
            "error": str(e),
        }


# Common SIC codes and their peer groups for major industries
# Format: SIC -> list of common tickers in that industry
SIC_PEER_GROUPS: dict[str, list[str]] = {
    # Technology - Computer Hardware & Software
    "3571": ["AAPL", "HPQ", "DELL", "HPE"],  # Electronic Computers
    "7370": ["MSFT", "ORCL", "CRM", "SAP", "ADBE", "NOW", "INTU"],  # Computer Programming Services
    "7372": ["MSFT", "ORCL", "SAP", "ADBE", "CRM"],  # Prepackaged Software
    "7374": ["GOOGL", "META", "AMZN", "CRM", "NOW"],  # Computer Processing/Data Prep
    "7379": ["IBM", "ACN", "INFY", "WIT"],  # Computer Related Services

    # Internet & Communication Services
    "7370_INTERNET": ["GOOGL", "META", "SNAP", "PINS", "TWTR"],  # Internet Services (suffix to avoid dupe)
    "4813": ["T", "VZ", "TMUS", "CMCSA"],  # Telephone Communications
    "4841": ["NFLX", "DIS", "PARA", "WBD", "CMCSA"],  # Cable & TV Services

    # Retail Trade
    "5311": ["WMT", "TGT", "COST", "BJ", "DG"],  # Department Stores
    "5331": ["WMT", "TGT", "COST", "DG", "DLTR"],  # Variety Stores
    "5912": ["CVS", "WBA", "RAD"],  # Drug Stores
    "5961": ["AMZN", "EBAY", "ETSY", "W", "CHWY"],  # Catalog & Mail-Order Houses

    # Automotive
    "3711": ["F", "GM", "TSLA", "TM", "HMC", "STLA"],  # Motor Vehicles
    "3714": ["BWA", "APTV", "LEA", "MGA"],  # Motor Vehicle Parts

    # Financial Services - Banks
    "6021": ["JPM", "BAC", "WFC", "C", "USB"],  # National Commercial Banks
    "6022": ["PNC", "TFC", "KEY", "MTB", "CFG"],  # State Commercial Banks
    "6211": ["GS", "MS", "SCHW", "RJF"],  # Security Brokers/Dealers
    "6282": ["BLK", "BX", "KKR", "APO"],  # Investment Advisors

    # Healthcare & Pharmaceuticals
    "2834": ["JNJ", "PFE", "MRK", "ABBV", "LLY", "BMY"],  # Pharmaceutical Preparations
    "2836": ["AMGN", "GILD", "BIIB", "REGN", "VRTX"],  # Biological Products
    "3841": ["MDT", "ABT", "SYK", "BSX", "BDX"],  # Surgical & Medical Instruments
    "6324": ["UNH", "ELV", "CI", "HUM", "CNC"],  # Health Insurance

    # Oil & Gas
    "1311": ["XOM", "CVX", "COP", "EOG", "OXY", "PXD"],  # Crude Petroleum & Natural Gas
    "2911": ["XOM", "CVX", "VLO", "MPC", "PSX"],  # Petroleum Refining

    # Consumer Goods
    "2080": ["KO", "PEP", "MNST", "KDP"],  # Beverages
    "2844": ["PG", "CL", "EL", "CHD"],  # Perfumes/Cosmetics
    "2000": ["PG", "KO", "PEP", "MDLZ", "GIS", "K"],  # Food Products

    # Aerospace & Defense
    "3721": ["BA", "LMT", "GD", "NOC", "RTX"],  # Aircraft
    "3760": ["LMT", "RTX", "NOC", "GD", "BA"],  # Guided Missiles & Space

    # Semiconductors
    "3674": ["NVDA", "AMD", "INTC", "AVGO", "QCOM", "TXN", "MU"],  # Semiconductors

    # Entertainment & Media
    "7812": ["DIS", "NFLX", "WBD", "PARA", "CMCSA"],  # Motion Picture Production
}


def _get_sic_based_peers(sic: str | None, ticker: str, limit: int) -> list[str]:
    """
    Get peer companies based on SIC code.

    Falls back to curated list for well-known companies if SIC not found.
    """
    if sic:
        # Look for exact SIC match
        peers = SIC_PEER_GROUPS.get(sic, [])
        if peers:
            # Remove the company itself from peers
            return [p for p in peers if p != ticker.upper()][:limit]

        # Try 2-digit SIC prefix match (broader industry)
        sic_prefix = sic[:2] if len(sic) >= 2 else sic
        for sic_code, peer_list in SIC_PEER_GROUPS.items():
            if sic_code.startswith(sic_prefix):
                peers = [p for p in peer_list if p != ticker.upper()]
                if peers:
                    return peers[:limit]

    # Fallback to curated peer groups for well-known companies
    curated_peers = {
        "AAPL": ["MSFT", "GOOGL", "META", "AMZN", "NVDA"],
        "MSFT": ["AAPL", "GOOGL", "META", "ORCL", "CRM"],
        "GOOGL": ["META", "MSFT", "AMZN", "NFLX", "SNAP"],
        "AMZN": ["WMT", "TGT", "EBAY", "COST", "GOOGL"],
        "TSLA": ["F", "GM", "RIVN", "LCID", "NIO"],
        "JPM": ["BAC", "WFC", "C", "GS", "MS"],
        "JNJ": ["PFE", "MRK", "ABBV", "LLY", "BMY"],
        "XOM": ["CVX", "COP", "OXY", "EOG", "PXD"],
        "NVDA": ["AMD", "INTC", "AVGO", "QCOM", "TXN"],
    }

    return curated_peers.get(ticker.upper(), [])[:limit]


@registry.register(
    name="get_sector_peers",
    description="Find peer companies in the same sector/industry based on SIC code. Returns companies with similar business classifications for competitive analysis.",
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

        # Get peers based on SIC code
        peers = _get_sic_based_peers(company.sic, ticker, limit)

        # If we found SIC-based peers, include the industry description
        industry_note = ""
        if company.sic and company.sic_description:
            industry_note = f"Industry: {company.sic_description} (SIC {company.sic})"
        elif peers:
            industry_note = "Peers selected based on market sector classification"

        return {
            "success": True,
            "ticker": ticker.upper(),
            "company": company.name,
            "sic": company.sic,
            "sic_description": company.sic_description,
            "peers": peers,
            "peer_count": len(peers),
            "note": industry_note or "Limited peer data available for this company.",
        }

    except Exception as e:
        logger.error(f"Peer lookup failed: {e}")
        return {
            "success": False,
            "error": str(e),
        }
