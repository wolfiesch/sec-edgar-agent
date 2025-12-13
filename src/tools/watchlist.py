"""Watchlist management and monitoring tools."""

import json
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from src.config import settings
from src.data.edgar_client import get_edgar_client
from src.tools.registry import registry

logger = logging.getLogger(__name__)

# Watchlist storage path
WATCHLIST_FILE = Path(settings.cache_dir) / "watchlist.json"


def _load_watchlist() -> dict[str, Any]:
    """Load watchlist from file."""
    if WATCHLIST_FILE.exists():
        try:
            with open(WATCHLIST_FILE) as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except (json.JSONDecodeError, OSError):
            pass
    return {"companies": {}, "last_check": None}


def _save_watchlist(data: dict[str, Any]) -> None:
    """Save watchlist to file."""
    WATCHLIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


@registry.register(
    name="add_to_watchlist",
    description="Add a company to your watchlist for monitoring new filings and insider activity.",
    parameters={
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "Stock ticker symbol to watch",
            },
            "watch_forms": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Form types to monitor",
                "default": ["10-K", "10-Q", "8-K", "4"],
            },
            "notes": {
                "type": "string",
                "description": "Optional notes about why you're watching this company",
            },
        },
        "required": ["ticker"],
    },
)
def add_to_watchlist(
    ticker: str,
    watch_forms: list[str] | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Add a company to the watchlist."""
    if watch_forms is None:
        watch_forms = ["10-K", "10-Q", "8-K", "4"]

    client = get_edgar_client()

    try:
        # Verify company exists
        company = client.get_company(ticker)

        watchlist = _load_watchlist()

        watchlist["companies"][ticker.upper()] = {
            "name": company.name,
            "cik": company.cik,
            "watch_forms": watch_forms,
            "notes": notes,
            "added": datetime.now().isoformat(),
            "last_filing_seen": None,
        }

        _save_watchlist(watchlist)

        return {
            "success": True,
            "message": f"Added {company.name} ({ticker.upper()}) to watchlist",
            "watching": watch_forms,
        }

    except Exception as e:
        logger.error(f"Failed to add to watchlist: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@registry.register(
    name="remove_from_watchlist",
    description="Remove a company from your watchlist.",
    parameters={
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "Stock ticker symbol to remove",
            },
        },
        "required": ["ticker"],
    },
)
def remove_from_watchlist(ticker: str) -> dict[str, Any]:
    """Remove a company from the watchlist."""
    watchlist = _load_watchlist()

    ticker_upper = ticker.upper()
    if ticker_upper in watchlist["companies"]:
        removed = watchlist["companies"].pop(ticker_upper)
        _save_watchlist(watchlist)
        return {
            "success": True,
            "message": f"Removed {removed.get('name', ticker_upper)} from watchlist",
        }
    else:
        return {
            "success": False,
            "error": f"{ticker_upper} is not in watchlist",
        }


@registry.register(
    name="get_watchlist",
    description="Get all companies currently on your watchlist.",
    parameters={
        "type": "object",
        "properties": {},
    },
)
def get_watchlist() -> dict[str, Any]:
    """Get current watchlist."""
    watchlist = _load_watchlist()

    companies = []
    for ticker, data in watchlist["companies"].items():
        companies.append({
            "ticker": ticker,
            "name": data.get("name"),
            "watching": data.get("watch_forms", []),
            "notes": data.get("notes"),
            "added": data.get("added"),
        })

    return {
        "success": True,
        "count": len(companies),
        "companies": companies,
    }


@registry.register(
    name="check_watchlist_updates",
    description="Check for new filings from watchlist companies since last check.",
    parameters={
        "type": "object",
        "properties": {
            "days_back": {
                "type": "integer",
                "description": "How many days back to check for filings",
                "default": 7,
            },
        },
    },
)
def check_watchlist_updates(days_back: int = 7) -> dict[str, Any]:
    """Check for new filings from watchlist companies."""
    watchlist = _load_watchlist()

    if not watchlist["companies"]:
        return {
            "success": True,
            "message": "Watchlist is empty. Add companies with add_to_watchlist.",
            "updates": [],
        }

    client = get_edgar_client()
    cutoff_date = date.today() - timedelta(days=days_back)
    updates = []

    for ticker, data in watchlist["companies"].items():
        watch_forms = data.get("watch_forms", ["10-K", "10-Q", "8-K"])

        for form_type in watch_forms:
            try:
                filings = client.get_filings(
                    ticker=ticker,
                    form_type=form_type,
                    limit=5,
                    start_date=cutoff_date,
                )

                for filing in filings:
                    updates.append({
                        "ticker": ticker,
                        "company": data.get("name"),
                        "form_type": filing.form_type,
                        "filing_date": filing.filing_date.isoformat(),
                        "accession_number": filing.accession_number,
                    })

            except Exception as e:
                logger.warning(f"Failed to check {ticker} {form_type}: {e}")

    # Update last check time
    watchlist["last_check"] = datetime.now().isoformat()
    _save_watchlist(watchlist)

    # Sort by date (most recent first)
    updates.sort(key=lambda x: x["filing_date"], reverse=True)

    return {
        "success": True,
        "period": f"Last {days_back} days",
        "update_count": len(updates),
        "updates": updates,
    }


@registry.register(
    name="generate_watchlist_summary",
    description="Generate a summary report of your watchlist companies including recent activity.",
    parameters={
        "type": "object",
        "properties": {},
    },
)
def generate_watchlist_summary() -> dict[str, Any]:
    """Generate summary for all watchlist companies."""
    watchlist = _load_watchlist()

    if not watchlist["companies"]:
        return {
            "success": True,
            "message": "Watchlist is empty",
            "summaries": [],
        }

    client = get_edgar_client()
    summaries = []

    for ticker, data in watchlist["companies"].items():
        try:
            # Get recent filings
            filings = client.get_filings(ticker, "10-K", limit=1)
            recent_10k = filings[0] if filings else None

            filings_8k = client.get_filings(ticker, "8-K", limit=3)

            # Get insider activity
            insider_txns = client.get_insider_transactions(ticker, limit=10)

            # Summarize insider activity
            insider_summary = {"buys": 0, "sells": 0, "buy_shares": 0.0, "sell_shares": 0.0}
            for txn in insider_txns:
                if txn.transaction_type == "P":
                    insider_summary["buys"] += 1
                    insider_summary["buy_shares"] += txn.shares
                elif txn.transaction_type == "S":
                    insider_summary["sells"] += 1
                    insider_summary["sell_shares"] += txn.shares

            summaries.append({
                "ticker": ticker,
                "name": data.get("name"),
                "notes": data.get("notes"),
                "latest_10k": {
                    "date": recent_10k.filing_date.isoformat() if recent_10k else None,
                    "accession": recent_10k.accession_number if recent_10k else None,
                } if recent_10k else None,
                "recent_8k_count": len(filings_8k),
                "insider_activity": insider_summary,
            })

        except Exception as e:
            logger.warning(f"Failed to summarize {ticker}: {e}")
            summaries.append({
                "ticker": ticker,
                "name": data.get("name"),
                "error": str(e),
            })

    return {
        "success": True,
        "generated": datetime.now().isoformat(),
        "company_count": len(summaries),
        "summaries": summaries,
    }
