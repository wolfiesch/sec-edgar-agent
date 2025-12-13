"""Endpoints for retrieving filing metadata and available sections."""
from typing import Any
from edgar import Company
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session

from src.api.dependencies import get_db
from src.tools.analysis import detect_risk_changes
from src.utils.exceptions import FilingNotFound, SecApiError  # type: ignore
from ..models.responses import FilingResponse

router = APIRouter()


class DiffRequest(BaseModel):
    """Request to compare filings between two years."""
    ticker: str = Field(..., description="Stock ticker symbol")
    year1: int = Field(..., description="First year (earlier)")
    year2: int = Field(..., description="Second year (later)")

@router.get("/{ticker}/{form_type}", response_model=FilingResponse)
async def get_filing(
    ticker: str,
    form_type: str,
    year: int | None = Query(None, description="Filing year (default: latest)")
) -> dict[str, Any]:
    """
    Retrieve metadata for a specific SEC filing.

    Returns filing information with citation and download URL.
    """
    try:
        company = Company(ticker)
        filings = company.get_filings(form=form_type)

        if not filings:
            raise FilingNotFound(ticker=ticker, form_type=form_type)

        if year:
            # Filter by year
            filings = [f for f in filings if f.filing_date.year == year]

        if not filings:
            raise HTTPException(
                status_code=404,
                detail=f"No {form_type} filings found for {ticker}",
            )

        filing = filings[0]  # Latest

        return {
            "ticker": ticker,
            "form_type": form_type,
            "filing_date": str(filing.filing_date),
            "accession_no": filing.accession_no,
            "url": filing.url,
            "citation": f"[{ticker} {form_type} {filing.filing_date.year}]",
            "sections_available": [
                "Item 1",
                "Item 1A",
                "Item 7",
                "Item 8",
            ],  # Can extract dynamically
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





@router.get("/{accession_number}/html")
async def download_filing_html(
    accession_number: str,
    db: Session = Depends(get_db),
) -> str:
    """
    Download the HTML content of a filing.
    """
    # TODO: Implement actual HTML retrieval logic using accession_number and db
    return f"<html><body><h1>HTML content for {accession_number}</h1></body></html>"


@router.get("/{ticker}/{form_type}/sections")
async def list_sections(
    ticker: str, form_type: str, year: int | None = None
) -> dict[str, Any]:
    """List available sections in a filing (for discovery)."""
    # TODO: Implement section extraction
    return {
        "ticker": ticker,
        "form_type": form_type,
        "sections": ["Item 1", "Item 1A", "Item 7", "Item 8", "Item 15"],
    }


@router.post("/diff")
async def compare_filings(request: DiffRequest) -> dict[str, Any]:
    """
    Compare risk factors between two annual filings.

    Identifies new, removed, and modified risk factors between years.
    """
    try:
        result = detect_risk_changes(
            ticker=request.ticker,
            year1=request.year1,
            year2=request.year2,
        )
        return dict(result)
    except Exception as e:
        raise SecApiError(f"Failed to compare filings: {str(e)}")
