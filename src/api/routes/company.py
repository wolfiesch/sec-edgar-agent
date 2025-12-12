import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.data.edgar_client import get_edgar_client

logger = logging.getLogger(__name__)
router = APIRouter()


class CompanyInfo(BaseModel):
    ticker: str
    cik: str
    name: str
    sic: str | None = None
    sic_description: str | None = None


class FilingSummary(BaseModel):
    accession_number: str
    form_type: str
    filing_date: str
    primary_document: str | None = None
    url: str | None = None


@router.get("/{ticker}", response_model=CompanyInfo)
async def get_company_info(ticker: str):
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
    except Exception as e:
        logger.error(f"Error fetching company {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker}/filings", response_model=list[FilingSummary])
async def get_company_filings(ticker: str, form_type: str | None = "10-K", limit: int = 10):
    """Get recent filings for a company."""
    try:
        client = get_edgar_client()
        filings = client.get_filings(ticker, form_type=form_type, limit=limit)

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
    except Exception as e:
        logger.error(f"Error fetching filings for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
