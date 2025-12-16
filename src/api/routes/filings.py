"""Endpoints for retrieving filing metadata and available sections."""
import logging
from typing import Any

import httpx
from edgar import Company
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session

from src.api.dependencies import get_db
from src.api.exceptions import FilingNotFound, SecApiError
from src.config import settings
from src.tools.analysis import detect_risk_changes

from ..models.responses import FilingResponse

logger = logging.getLogger(__name__)

router = APIRouter()


class DiffRequest(BaseModel):
    """Request to compare filings between two years."""
    ticker: str = Field(..., description="Stock ticker symbol")
    year1: int = Field(..., description="First year (earlier)")
    year2: int = Field(..., description="Second year (later)")


# NOTE: Route order matters in FastAPI! More specific routes must come before
# more general ones. The routes below are ordered from most specific to least.


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


@router.get("/{accession_number}/html")
async def download_filing_html(
    accession_number: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Download the HTML content of a filing by accession number.

    The accession number format is: 0000320193-24-000123
    where the first 10 digits are the CIK (zero-padded).
    """
    try:
        # Extract CIK from accession number (first 10 digits before first dash)
        parts = accession_number.split("-")
        if len(parts) != 3:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid accession number format: {accession_number}. Expected format: 0000320193-24-000123"
            )

        cik = parts[0].lstrip("0") or "0"
        accession_no_dashes = accession_number.replace("-", "")

        # Fetch the filing index from SEC EDGAR
        index_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_no_dashes}/index.json"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                index_url,
                headers={"User-Agent": settings.sec_user_agent},
            )
            response.raise_for_status()
            index_data = response.json()

        # Find the primary document (usually the main filing HTML)
        directory = index_data.get("directory", {})
        items = directory.get("item", [])

        primary_doc = None

        # Look for the primary document (typically ends with .htm and is the main filing)
        for item in items:
            name = item.get("name", "")
            # Primary documents are usually the largest .htm file or explicitly marked
            if name.endswith(".htm") and not name.startswith("R"):
                # Skip R*.htm files (these are usually exhibit references)
                if item.get("type") in ["10-K", "10-Q", "8-K", "4", "DEF 14A"] or "filing" in name.lower():
                    primary_doc = name
                    break
                elif primary_doc is None:
                    primary_doc = name

        if not primary_doc:
            # Fallback: find any .htm file
            for item in items:
                if item.get("name", "").endswith(".htm"):
                    primary_doc = item["name"]
                    break

        if not primary_doc:
            return {
                "success": False,
                "error": "No HTML document found in filing",
                "accession_number": accession_number,
                "available_files": [item.get("name") for item in items],
            }

        # Fetch the HTML content
        primary_doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_no_dashes}/{primary_doc}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            html_response = await client.get(
                primary_doc_url,
                headers={"User-Agent": settings.sec_user_agent},
            )
            html_response.raise_for_status()
            html_content = html_response.text

        return {
            "success": True,
            "accession_number": accession_number,
            "cik": cik,
            "document_name": primary_doc,
            "document_url": primary_doc_url,
            "html": html_content,
            "content_length": len(html_content),
        }

    except httpx.HTTPStatusError as e:
        logger.error(f"Failed to fetch filing HTML: {e}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"SEC EDGAR returned error: {e.response.status_code}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching filing HTML: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker}/{form_type}/sections")
async def list_sections(
    ticker: str, form_type: str, year: int | None = None
) -> dict[str, Any]:
    """
    List available sections in a filing (for discovery).

    Dynamically detects which sections are present in the filing.
    """
    try:
        company = Company(ticker.upper())
        filings = company.get_filings(form=form_type)

        if not filings:
            raise FilingNotFound(ticker=ticker, form_type=form_type)

        # Filter by year if specified
        if year:
            filings = [f for f in filings if f.filing_date.year == year]

        if not filings:
            raise FilingNotFound(ticker=ticker, form_type=form_type, year=year)

        filing = filings[0]

        # Define section mappings based on form type
        if form_type.upper() in ["10-K", "10-K/A"]:
            potential_sections = [
                ("Item 1", "Business"),
                ("Item 1A", "Risk Factors"),
                ("Item 1B", "Unresolved Staff Comments"),
                ("Item 2", "Properties"),
                ("Item 3", "Legal Proceedings"),
                ("Item 4", "Mine Safety Disclosures"),
                ("Item 5", "Market for Registrant's Common Equity"),
                ("Item 6", "Selected Financial Data"),
                ("Item 7", "Management's Discussion and Analysis (MD&A)"),
                ("Item 7A", "Quantitative and Qualitative Disclosures About Market Risk"),
                ("Item 8", "Financial Statements and Supplementary Data"),
                ("Item 9", "Changes in and Disagreements With Accountants"),
                ("Item 9A", "Controls and Procedures"),
                ("Item 9B", "Other Information"),
                ("Item 10", "Directors, Executive Officers and Corporate Governance"),
                ("Item 11", "Executive Compensation"),
                ("Item 12", "Security Ownership"),
                ("Item 13", "Certain Relationships and Related Transactions"),
                ("Item 14", "Principal Accountant Fees and Services"),
                ("Item 15", "Exhibits and Financial Statement Schedules"),
            ]
        elif form_type.upper() in ["10-Q", "10-Q/A"]:
            potential_sections = [
                ("Item 1", "Financial Statements"),
                ("Item 2", "Management's Discussion and Analysis (MD&A)"),
                ("Item 3", "Quantitative and Qualitative Disclosures About Market Risk"),
                ("Item 4", "Controls and Procedures"),
                ("Part II Item 1", "Legal Proceedings"),
                ("Part II Item 1A", "Risk Factors"),
                ("Part II Item 2", "Unregistered Sales of Equity Securities"),
                ("Part II Item 3", "Defaults Upon Senior Securities"),
                ("Part II Item 4", "Mine Safety Disclosures"),
                ("Part II Item 5", "Other Information"),
                ("Part II Item 6", "Exhibits"),
            ]
        elif form_type.upper() in ["8-K", "8-K/A"]:
            potential_sections = [
                ("Item 1.01", "Entry into a Material Definitive Agreement"),
                ("Item 1.02", "Termination of a Material Definitive Agreement"),
                ("Item 2.01", "Completion of Acquisition or Disposition of Assets"),
                ("Item 2.02", "Results of Operations and Financial Condition"),
                ("Item 2.03", "Creation of Direct Financial Obligation"),
                ("Item 2.04", "Triggering Events That Accelerate Obligations"),
                ("Item 2.05", "Costs Associated with Exit or Disposal Activities"),
                ("Item 2.06", "Material Impairments"),
                ("Item 3.01", "Notice of Delisting or Failure to Satisfy Listing Requirements"),
                ("Item 3.02", "Unregistered Sales of Equity Securities"),
                ("Item 3.03", "Material Modification to Rights of Security Holders"),
                ("Item 4.01", "Changes in Registrant's Certifying Accountant"),
                ("Item 4.02", "Non-Reliance on Previously Issued Financial Statements"),
                ("Item 5.01", "Changes in Control of Registrant"),
                ("Item 5.02", "Departure/Election of Directors or Officers"),
                ("Item 5.03", "Amendments to Articles of Incorporation or Bylaws"),
                ("Item 5.07", "Submission of Matters to a Vote of Security Holders"),
                ("Item 7.01", "Regulation FD Disclosure"),
                ("Item 8.01", "Other Events"),
                ("Item 9.01", "Financial Statements and Exhibits"),
            ]
        else:
            # Generic fallback
            potential_sections = [
                ("Item 1", "Primary Content"),
                ("Exhibits", "Exhibits"),
            ]

        # Try to detect which sections actually exist in the filing
        detected_sections = []
        try:
            # Get filing text for section detection
            text = filing.text() if hasattr(filing, "text") else ""
            text_upper = text.upper()

            for item_id, description in potential_sections:
                # Check if this section exists in the filing
                search_pattern = item_id.upper().replace(" ", r"\s*")
                if item_id.upper() in text_upper or search_pattern in text_upper:
                    detected_sections.append({
                        "id": item_id,
                        "description": description,
                    })
        except Exception as e:
            logger.warning(f"Could not detect sections dynamically: {e}")
            # Fallback to common sections
            if form_type.upper() in ["10-K", "10-K/A"]:
                detected_sections = [
                    {"id": "Item 1", "description": "Business"},
                    {"id": "Item 1A", "description": "Risk Factors"},
                    {"id": "Item 7", "description": "Management's Discussion and Analysis (MD&A)"},
                    {"id": "Item 8", "description": "Financial Statements and Supplementary Data"},
                    {"id": "Item 9A", "description": "Controls and Procedures"},
                ]
            elif form_type.upper() in ["10-Q", "10-Q/A"]:
                detected_sections = [
                    {"id": "Item 1", "description": "Financial Statements"},
                    {"id": "Item 2", "description": "Management's Discussion and Analysis (MD&A)"},
                ]
            else:
                detected_sections = [{"id": s[0], "description": s[1]} for s in potential_sections[:5]]

        return {
            "success": True,
            "ticker": ticker.upper(),
            "form_type": form_type,
            "filing_date": str(filing.filing_date),
            "accession_number": filing.accession_number,
            "sections": detected_sections,
            "section_count": len(detected_sections),
        }

    except FilingNotFound:
        raise
    except Exception as e:
        logger.error(f"Error listing sections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
            raise FilingNotFound(ticker=ticker, form_type=form_type, year=year)

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
    except FilingNotFound:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
