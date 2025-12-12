
from edgar import Company
from fastapi import APIRouter, Query

from ...utils.citations import create_citation_from_filing
from ..exceptions import FilingNotFound, SecApiError
from ..models.responses import FilingResponse

router = APIRouter()

@router.get("/{ticker}/{form_type}", response_model=FilingResponse)
async def get_filing(
    ticker: str,
    form_type: str,
    year: int | None = Query(None, description="Filing year (default: latest)")
):
    """
    Retrieve metadata for a specific SEC filing.

    Returns filing information with citation and download URL.
    """
    try:
        company = Company(ticker)
        filings = company.get_filings(form=form_type)

        if not filings:
            raise FilingNotFound(ticker=ticker, form_type=form_type)

        selected_filing = None
        if year:
            # Filter by year
            # Filing.filing_date is a date object
            for f in filings:
                if f.filing_date.year == year:
                    selected_filing = f
                    break
            if not selected_filing:
                raise FilingNotFound(ticker=ticker, form_type=form_type, year=year)
        else:
            selected_filing = filings[0] # Latest

        # Generate citation
        citation = create_citation_from_filing(selected_filing, ticker=ticker)

        # Build response
        # Using URL from filing object or generated one
        url = selected_filing.url if hasattr(selected_filing, 'url') else citation.source_url

        return FilingResponse(
            ticker=ticker,
            form_type=form_type,
            filing_date=str(selected_filing.filing_date),
            accession_no=selected_filing.accession_no,
            url=url or "",
            citation=citation.to_string(),
            sections_available=[
                "Item 1", "Item 1A", "Item 7", "Item 7A", "Item 8", "Item 9", "Item 9A"
            ] # Static list for demo, or extract if possible
        )

    except FilingNotFound:
        raise
    except Exception as e:
        raise SecApiError(f"Failed to fetch filing: {str(e)}")

@router.get("/{ticker}/{form_type}/sections")
async def list_sections(ticker: str, form_type: str, year: int | None = None):
    """List available sections in a filing (for discovery)."""
    # For demo, returning static common sections for 10-K
    return {
        "ticker": ticker,
        "form_type": form_type,
        "sections": ["Item 1", "Item 1A", "Item 7", "Item 8", "Item 15"]
    }
