"""Semantic search tools using vector store."""

import logging
from typing import Any

from src.data.edgar_client import get_edgar_client
from src.data.vector_store import get_vector_store
from src.tools.registry import registry

logger = logging.getLogger(__name__)


@registry.register(
    name="index_filing",
    description="Index a filing's sections for semantic search. Run this before using semantic search on a company's filings.",
    parameters={
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "Stock ticker symbol",
            },
            "form_type": {
                "type": "string",
                "description": "Form type to index",
                "default": "10-K",
            },
            "sections": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Sections to index (default: Risk Factors, MD&A)",
                "default": ["Risk Factors", "MD&A"],
            },
        },
        "required": ["ticker"],
    },
)
def index_filing(
    ticker: str,
    form_type: str = "10-K",
    sections: list[str] | None = None,
) -> dict[str, Any]:
    """
    Index a filing for semantic search.

    Args:
        ticker: Stock ticker symbol.
        form_type: Form type to index (e.g., '10-K', '10-Q').
        sections: List of sections to index (default: Risk Factors, MD&A).

    Returns:
        Dictionary containing indexing status and details.
    """
    if sections is None:
        sections = ["Risk Factors", "MD&A"]

    client = get_edgar_client()
    vector_store = get_vector_store()

    try:
        # Get most recent filing
        filings = client.get_filings(ticker, form_type, limit=1)
        if not filings:
            return {
                "success": False,
                "error": f"No {form_type} filings found for {ticker}",
            }

        filing = filings[0]
        edgar_filing = client.get_filing_by_accession(ticker, filing.accession_number)

        if not edgar_filing:
            return {
                "success": False,
                "error": "Could not fetch filing content",
            }

        indexed_sections = []

        # Try to get each section
        for section in sections:
            try:
                # Get section content
                obj = edgar_filing.obj()
                content = None

                # Map section names to attributes
                section_map = {
                    "Risk Factors": "item_1a",
                    "Business": "item_1",
                    "MD&A": "item_7",
                    "Financial Statements": "item_8",
                }

                attr_name = section_map.get(section, section.lower().replace(" ", "_"))
                if hasattr(obj, attr_name):
                    content = str(getattr(obj, attr_name))

                if content and len(content) > 100:
                    vector_store.add_filing_section(
                        ticker=ticker,
                        accession_number=filing.accession_number,
                        section_name=section,
                        content=content,
                        metadata={
                            "form_type": form_type,
                            "filing_date": filing.filing_date.isoformat(),
                        },
                    )
                    indexed_sections.append({
                        "section": section,
                        "length": len(content),
                    })

            except Exception as e:
                logger.warning(f"Failed to index section {section}: {e}")

        return {
            "success": True,
            "ticker": ticker.upper(),
            "filing": {
                "form_type": form_type,
                "filing_date": filing.filing_date.isoformat(),
                "accession_number": filing.accession_number,
            },
            "indexed_sections": indexed_sections,
        }

    except Exception as e:
        logger.error(f"Indexing failed: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@registry.register(
    name="semantic_search",
    description="Search indexed filings using natural language. Finds relevant sections based on meaning, not just keywords.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language search query",
            },
            "ticker": {
                "type": "string",
                "description": "Filter results to specific company (optional)",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum results to return",
                "default": 5,
            },
        },
        "required": ["query"],
    },
)
def semantic_search(
    query: str,
    ticker: str | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    """
    Search filings using semantic similarity.

    Args:
        query: Natural language search query.
        ticker: Optional stock ticker symbol to filter by.
        limit: Maximum results to return (default: 5).

    Returns:
        Dictionary containing search results with relevance scores.
    """
    vector_store = get_vector_store()

    try:
        results = vector_store.search(
            query=query,
            ticker=ticker,
            limit=limit,
        )

        if not results:
            return {
                "success": True,
                "message": "No matching content found. Try indexing some filings first with index_filing.",
                "results": [],
            }

        formatted_results = []
        for r in results:
            formatted_results.append({
                "ticker": r["metadata"].get("ticker"),
                "section": r["metadata"].get("section_name"),
                "filing_date": r["metadata"].get("filing_date"),
                "relevance_score": 1 - (r["distance"] or 0),  # Convert distance to similarity
                "excerpt": r["content"][:500] + "..." if len(r["content"]) > 500 else r["content"],
            })

        return {
            "success": True,
            "query": query,
            "result_count": len(formatted_results),
            "results": formatted_results,
        }

    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@registry.register(
    name="find_similar_disclosures",
    description="Find companies with similar disclosures to a given company's filing section. Useful for finding peers with similar risks.",
    parameters={
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "Source company ticker",
            },
            "section": {
                "type": "string",
                "description": "Section to find similarities for",
                "default": "Risk Factors",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum similar companies to return",
                "default": 3,
            },
        },
        "required": ["ticker"],
    },
)
def find_similar_disclosures(
    ticker: str,
    section: str = "Risk Factors",
    limit: int = 3,
) -> dict[str, Any]:
    """
    Find companies with similar disclosures.

    Args:
        ticker: Source company ticker.
        section: Section to find similarities for (default: 'Risk Factors').
        limit: Maximum similar companies to return (default: 3).

    Returns:
        Dictionary containing the source section and similar companies' sections.
    """
    client = get_edgar_client()
    vector_store = get_vector_store()

    try:
        # Get the source company's section content
        filings = client.get_filings(ticker, "10-K", limit=1)
        if not filings:
            return {
                "success": False,
                "error": f"No 10-K filings found for {ticker}",
            }

        filing = filings[0]
        edgar_filing = client.get_filing_by_accession(ticker, filing.accession_number)

        if not edgar_filing:
            return {
                "success": False,
                "error": "Could not fetch filing content",
            }

        # Get section content
        obj = edgar_filing.obj()
        section_map = {
            "Risk Factors": "item_1a",
            "Business": "item_1",
            "MD&A": "item_7",
        }

        attr_name = section_map.get(section, section.lower().replace(" ", "_"))
        content = None
        if hasattr(obj, attr_name):
            content = str(getattr(obj, attr_name))

        if not content:
            return {
                "success": False,
                "error": f"Could not extract {section} from filing",
            }

        # Search for similar content from other companies
        similar = vector_store.search_similar(
            content=content[:8000],
            exclude_ticker=ticker,
            limit=limit,
        )

        return {
            "success": True,
            "source": {
                "ticker": ticker.upper(),
                "section": section,
                "filing_date": filing.filing_date.isoformat(),
            },
            "similar_companies": [
                {
                    "ticker": s["metadata"].get("ticker"),
                    "section": s["metadata"].get("section_name"),
                    "similarity_score": 1 - (s["distance"] or 0),
                    "excerpt": s["content"],
                }
                for s in similar
            ],
        }

    except Exception as e:
        logger.error(f"Similar disclosure search failed: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@registry.register(
    name="list_indexed_filings",
    description="List all filings that have been indexed for semantic search.",
    parameters={
        "type": "object",
        "properties": {},
    },
)
def list_indexed_filings() -> dict[str, Any]:
    """
    List indexed filings.

    Returns:
        Dictionary containing a summary of all indexed filings grouped by ticker.
    """
    vector_store = get_vector_store()

    try:
        filings = vector_store.get_indexed_filings()

        # Group by ticker
        by_ticker: dict[str, list[dict]] = {}
        for f in filings:
            ticker = f.get("ticker", "Unknown")
            if ticker not in by_ticker:
                by_ticker[ticker] = []
            by_ticker[ticker].append(f)

        return {
            "success": True,
            "total_indexed": len(filings),
            "by_ticker": by_ticker,
        }

    except Exception as e:
        logger.error(f"Failed to list indexed filings: {e}")
        return {
            "success": False,
            "error": str(e),
        }
