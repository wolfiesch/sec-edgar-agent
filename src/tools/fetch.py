"""Fetch tools for retrieving filing content."""

import logging
from typing import Any

from src.data.edgar_client import get_edgar_client
from src.data.models import Citation
from src.tools.registry import registry

logger = logging.getLogger(__name__)


@registry.register(
    name="get_filing_document",
    description="Fetch the full text content of a specific SEC filing. Use this to read the actual document.",
    parameters={
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "Stock ticker symbol",
            },
            "accession_number": {
                "type": "string",
                "description": "Filing accession number (e.g., '0000320193-24-000123')",
            },
            "max_length": {
                "type": "integer",
                "description": "Maximum characters to return (for large filings)",
                "default": 50000,
            },
        },
        "required": ["ticker", "accession_number"],
    },
)
def get_filing_document(
    ticker: str,
    accession_number: str,
    max_length: int = 50000,
) -> dict[str, Any]:
    """Fetch the text content of a filing."""
    client = get_edgar_client()
    filing = client.get_filing_by_accession(ticker, accession_number)

    if not filing:
        return {
            "error": f"Filing {accession_number} not found for {ticker}",
            "success": False,
        }

    try:
        # Get the filing text content
        text = filing.text() if hasattr(filing, "text") else str(filing)

        # Truncate if too long
        truncated = len(text) > max_length
        if truncated:
            text = text[:max_length] + "\n\n[... truncated ...]"

        citation = Citation(
            ticker=ticker.upper(),
            form_type=filing.form,
            filing_date=filing.filing_date,
            accession_number=accession_number,
        )

        return {
            "success": True,
            "ticker": ticker.upper(),
            "form_type": filing.form,
            "filing_date": filing.filing_date.isoformat(),
            "accession_number": accession_number,
            "content": text,
            "truncated": truncated,
            "total_length": len(filing.text()) if hasattr(filing, "text") else len(str(filing)),
            "citations": [citation],
        }

    except Exception as e:
        logger.error(f"Failed to fetch filing content: {e}")
        return {
            "error": str(e),
            "success": False,
        }


@registry.register(
    name="get_filing_section",
    description="Extract a specific section from a 10-K or 10-Q filing (e.g., Risk Factors, MD&A)",
    parameters={
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "Stock ticker symbol",
            },
            "accession_number": {
                "type": "string",
                "description": "Filing accession number",
            },
            "section": {
                "type": "string",
                "description": "Section to extract",
                "enum": [
                    "Business",
                    "Risk Factors",
                    "Properties",
                    "Legal Proceedings",
                    "MD&A",
                    "Financial Statements",
                    "Controls and Procedures",
                ],
            },
        },
        "required": ["ticker", "accession_number", "section"],
    },
)
def get_filing_section(
    ticker: str,
    accession_number: str,
    section: str,
) -> dict[str, Any]:
    """Extract a specific section from a filing."""
    client = get_edgar_client()
    filing = client.get_filing_by_accession(ticker, accession_number)

    if not filing:
        return {
            "error": f"Filing {accession_number} not found for {ticker}",
            "success": False,
        }

    # Map friendly names to item numbers
    section_map = {
        "Business": "Item 1",
        "Risk Factors": "Item 1A",
        "Properties": "Item 2",
        "Legal Proceedings": "Item 3",
        "MD&A": "Item 7",
        "Financial Statements": "Item 8",
        "Controls and Procedures": "Item 9A",
    }

    item = section_map.get(section, section)

    try:
        # Try to get the TenK/TenQ object for section extraction
        obj = filing.obj()

        # edgartools TenK objects have section accessors
        content = None
        if hasattr(obj, item.lower().replace(" ", "_")):
            content = getattr(obj, item.lower().replace(" ", "_"))
        elif hasattr(obj, "get_section"):
            content = obj.get_section(item)

        if content is None:
            # Fallback: search in text
            text = filing.text() if hasattr(filing, "text") else str(filing)
            # Simple section extraction (can be improved)
            item_upper = item.upper()
            start_idx = text.upper().find(item_upper)
            if start_idx != -1:
                # Find next item or end
                end_idx = len(text)
                for next_item in ["ITEM 1A", "ITEM 1B", "ITEM 2", "ITEM 3", "ITEM 4", "ITEM 5", "ITEM 6", "ITEM 7", "ITEM 7A", "ITEM 8", "ITEM 9", "ITEM 9A"]:
                    if next_item != item_upper:
                        next_idx = text.upper().find(next_item, start_idx + 100)
                        if next_idx != -1 and next_idx < end_idx:
                            end_idx = next_idx
                content = text[start_idx:end_idx]

        if content:
            content_str = str(content)
            # Limit content size
            if len(content_str) > 30000:
                content_str = content_str[:30000] + "\n\n[... truncated ...]"

            citation = Citation(
                ticker=ticker.upper(),
                form_type=filing.form,
                filing_date=filing.filing_date,
                section=section,
                accession_number=accession_number,
            )

            return {
                "success": True,
                "ticker": ticker.upper(),
                "section": section,
                "item": item,
                "content": content_str,
                "citations": [citation],
            }
        else:
            return {
                "success": False,
                "error": f"Section '{section}' not found in filing",
            }

    except Exception as e:
        logger.error(f"Failed to extract section: {e}")
        return {
            "error": str(e),
            "success": False,
        }


@registry.register(
    name="get_filing_exhibits",
    description="List exhibits attached to a filing (contracts, agreements, certifications)",
    parameters={
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "Stock ticker symbol",
            },
            "accession_number": {
                "type": "string",
                "description": "Filing accession number",
            },
        },
        "required": ["ticker", "accession_number"],
    },
)
def get_filing_exhibits(
    ticker: str,
    accession_number: str,
) -> dict[str, Any]:
    """List exhibits in a filing."""
    client = get_edgar_client()
    filing = client.get_filing_by_accession(ticker, accession_number)

    if not filing:
        return {
            "error": f"Filing {accession_number} not found for {ticker}",
            "success": False,
        }

    try:
        exhibits = []
        if hasattr(filing, "exhibits"):
            for exhibit in filing.exhibits:
                exhibits.append({
                    "number": getattr(exhibit, "number", ""),
                    "description": getattr(exhibit, "description", ""),
                    "url": getattr(exhibit, "url", ""),
                })

        return {
            "success": True,
            "ticker": ticker.upper(),
            "accession_number": accession_number,
            "exhibit_count": len(exhibits),
            "exhibits": exhibits,
        }

    except Exception as e:
        logger.error(f"Failed to get exhibits: {e}")
        return {
            "error": str(e),
            "success": False,
        }
