from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.api.models.requests import SearchRequest
from src.api.models.responses import SearchResponse, SearchResult
from src.data.edgar_client import get_edgar_client
from src.data.vector_store import FilingVectorStore, get_vector_store

router = APIRouter()


class FullTextSearchRequest(BaseModel):
    """Request model for full-text search."""

    query: str = Field(..., description="Search query (supports boolean operators: AND, OR, NOT, \"exact phrase\")")
    form_types: list[str] | None = Field(default=None, description="Filter by form types (e.g., ['10-K', '10-Q'])")
    start_date: date | None = Field(default=None, description="Filter filings from this date")
    end_date: date | None = Field(default=None, description="Filter filings up to this date")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum results to return")


class FullTextSearchResult(BaseModel):
    """Single result from full-text search."""

    ticker: str
    company_name: str
    form_type: str
    filing_date: str
    accession_number: str
    url: str | None


class FullTextSearchResponse(BaseModel):
    """Response model for full-text search."""

    query: str
    total: int
    results: list[FullTextSearchResult]


@router.post("/", response_model=SearchResponse)
async def search_filings(
    request: SearchRequest,
    vector_store: FilingVectorStore = Depends(get_vector_store),
):
    """
    Semantic search across SEC filings.
    """
    try:
        results = vector_store.search(
            query=request.query,
            ticker=request.ticker,
            section_name=request.section,
            limit=request.limit,
        )

        search_results = []
        for res in results:
            metadata = res.get("metadata", {})
            # Construct citation string
            ticker = metadata.get("ticker", "UNKNOWN")
            section = metadata.get("section_name", "Unknown Section")
            # Ideally we'd have year/form in metadata too, adding in Day 2
            citation = f"[{ticker} {section}]"

            search_results.append(
                SearchResult(
                    content=str(res["content"]),
                    citation=citation,
                    metadata=metadata,
                    distance=res.get("distance"),
                )
            )

        return SearchResponse(results=search_results, total=len(search_results))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/full-text", response_model=FullTextSearchResponse)
async def full_text_search(request: FullTextSearchRequest):
    """
    Full-text search across ALL SEC filings using SEC's EFTS API.

    This searches the complete text of all EDGAR filings submitted since 2001,
    including all attachments (exhibits).

    **Search Tips:**
    - Words are ANDed by default: `artificial intelligence` finds filings with both words
    - Use quotes for exact phrases: `"machine learning"`
    - Use OR for alternatives: `cybersecurity OR "data breach"`
    - Use NOT to exclude: `revenue NOT quarterly`

    **Example Queries:**
    - Find AI discussions in annual reports: `"artificial intelligence" -forms=10-K`
    - Find cybersecurity risk disclosures: `"cybersecurity" "risk factors"`
    - Find supply chain issues: `"supply chain" disruption`
    """
    try:
        client = get_edgar_client()

        filings = client.search_filings(
            query=request.query,
            form_types=request.form_types,
            start_date=request.start_date,
            end_date=request.end_date,
            limit=request.limit,
        )

        results = [
            FullTextSearchResult(
                ticker=f.company.ticker,
                company_name=f.company.name,
                form_type=f.form_type,
                filing_date=f.filing_date.isoformat(),
                accession_number=f.accession_number,
                url=f.url,
            )
            for f in filings
        ]

        return FullTextSearchResponse(
            query=request.query,
            total=len(results),
            results=results,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
