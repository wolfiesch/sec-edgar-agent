"""Company metadata endpoints backed by edgartools client."""
import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.data.edgar_client import get_edgar_client

logger = structlog.get_logger()
router = APIRouter()


class CompanyInfo(BaseModel):
    """Basic metadata returned for a given ticker."""
    ticker: str
    cik: str
    name: str
    sic: str | None = None
    sic_description: str | None = None


class FilingSummary(BaseModel):
    """Lightweight representation of a filing for listings."""
    accession_number: str
    form_type: str
    filing_date: str
    primary_document: str | None = None
    url: str | None = None


@router.get("/{ticker}", response_model=CompanyInfo)
async def get_company_info(ticker: str) -> CompanyInfo:
    """Get basic company information."""
    try:
        client = get_edgar_client()
        company = client.get_company(ticker)

        return CompanyInfo(
            ticker=company.ticker,
            cik=company.cik,
            name=company.name,
            sic=company.sic,
            sic_description=company.sic_description,
        )
    except ValueError as e:
        logger.warning("Invalid ticker requested", ticker=ticker, error=str(e))
        raise HTTPException(
            status_code=400,
            detail=f"Invalid ticker symbol '{ticker}'. Please provide a valid stock ticker."
        ) from e
    except LookupError as e:
        logger.info("Company not found", ticker=ticker)
        raise HTTPException(
            status_code=404,
            detail=f"Company with ticker '{ticker}' not found in SEC EDGAR database."
        ) from e
    except Exception as e:
        logger.exception("Failed to fetch company info", ticker=ticker, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch company information for '{ticker}': {e}"
        ) from e


@router.get("/{ticker}/filings", response_model=list[FilingSummary])
async def get_company_filings(ticker: str, form_type: str | None = "10-K", limit: int = 10) -> list[FilingSummary]:
    """Get recent filings for a company."""
    try:
        client = get_edgar_client()
        # Ensure form_type is a string for the client call
        search_form_type = form_type if form_type is not None else "10-K"
        filings = client.get_filings(ticker, form_type=search_form_type, limit=limit)

        result = []
        for filing in filings:
            result.append(FilingSummary(
                accession_number=filing.accession_number,
                form_type=filing.form_type,
                filing_date=str(filing.filing_date),
                primary_document=filing.primary_document,
                url=filing.url,
            ))

        return result
    except ValueError as e:
        logger.warning("Invalid filings request", ticker=ticker, form_type=form_type, error=str(e))
        raise HTTPException(
            status_code=400,
            detail=f"Invalid request parameters: {e}"
        ) from e
    except LookupError as e:
        logger.info("Company or filings not found", ticker=ticker, form_type=form_type)
        raise HTTPException(
            status_code=404,
            detail=f"No {form_type} filings found for '{ticker}'."
        ) from e
    except Exception as e:
        logger.exception("Failed to fetch filings", ticker=ticker, form_type=form_type, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch filings for '{ticker}': {e}"
        ) from e
