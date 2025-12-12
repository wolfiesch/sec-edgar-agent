"""SEC EDGAR API client wrapper using edgartools."""

import logging
import re
from datetime import date
from typing import Any

import edgar
import httpx
from edgar import Company as EdgarCompany
from edgar import Filing as EdgarFiling

from src.config import settings
from src.data.cache import get_cache
from src.data.models import Company, Filing, FinancialStatement, InsiderTransaction
from src.utils.rate_limiter import get_rate_limiter

logger = logging.getLogger(__name__)

# SEC EFTS (EDGAR Full-Text Search) API endpoint
EFTS_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"


class EdgarClient:
    """
    Wrapper around edgartools library with rate limiting and caching.

    Provides a clean interface to SEC EDGAR data.
    """

    def __init__(self):
        self.rate_limiter = get_rate_limiter(settings.sec_rate_limit)
        self.cache = get_cache()
        # Set edgartools identity (required by SEC)
        edgar.set_identity(settings.sec_user_agent)

    def _rate_limited_call(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        """Execute a function with rate limiting."""
        self.rate_limiter.wait()
        return func(*args, **kwargs)

    def get_company(self, ticker: str) -> Company:
        """
        Get company information by ticker symbol.

        Args:
            ticker: Stock ticker symbol (e.g., "AAPL")

        Returns:
            Company model with basic info
        """
        cache_key = f"company:{ticker.upper()}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return Company.model_validate(cached)

        logger.debug(f"Fetching company info for {ticker}")
        edgar_company: EdgarCompany = self._rate_limited_call(
            EdgarCompany, ticker.upper()
        )

        company = Company(
            cik=str(edgar_company.cik),
            ticker=ticker.upper(),
            name=edgar_company.name,
            sic=getattr(edgar_company, "sic", None),
            sic_description=getattr(edgar_company, "sic_description", None),
            exchange=getattr(edgar_company, "exchange", None),
        )

        self.cache.set(cache_key, company.model_dump())
        return company

    def get_filings(
        self,
        ticker: str,
        form_type: str = "10-K",
        limit: int = 5,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[Filing]:
        """
        Get filings for a company.

        Args:
            ticker: Stock ticker symbol
            form_type: Form type (10-K, 10-Q, 8-K, etc.)
            limit: Maximum number of filings to return
            start_date: Filter filings after this date
            end_date: Filter filings before this date

        Returns:
            List of Filing models
        """
        cache_key = f"filings:{ticker.upper()}:{form_type}:{limit}:{start_date}:{end_date}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return [Filing.model_validate(f) for f in cached]

        logger.debug(f"Fetching {form_type} filings for {ticker}")
        company = self.get_company(ticker)

        edgar_company: EdgarCompany = self._rate_limited_call(
            EdgarCompany, ticker.upper()
        )
        edgar_filings = edgar_company.get_filings(form=form_type)

        # Apply date filters if provided
        if start_date:
            edgar_filings = edgar_filings.filter(
                lambda f: f.filing_date >= start_date
            )
        if end_date:
            edgar_filings = edgar_filings.filter(
                lambda f: f.filing_date <= end_date
            )

        filings = []
        for ef in edgar_filings.head(limit):
            filing = Filing(
                accession_number=ef.accession_number,
                form_type=ef.form,
                filing_date=ef.filing_date,
                report_date=getattr(ef, "report_date", None),
                company=company,
                primary_document=getattr(ef, "primary_document", None),
                url=getattr(ef, "filing_href", None),
            )
            filings.append(filing)

        self.cache.set(cache_key, [f.model_dump(mode="json") for f in filings])
        return filings

    def get_filing_by_accession(
        self, ticker: str, accession_number: str
    ) -> EdgarFiling | None:
        """
        Get a specific filing by accession number.

        Returns the raw edgartools Filing for further processing.
        """
        logger.debug(f"Fetching filing {accession_number} for {ticker}")
        edgar_company: EdgarCompany = self._rate_limited_call(
            EdgarCompany, ticker.upper()
        )
        filings = edgar_company.get_filings()

        for filing in filings:
            if filing.accession_number == accession_number:
                return filing

        return None

    def get_financials(
        self,
        ticker: str,
        statement_type: str = "income_statement",
        periods: int = 4,
    ) -> list[FinancialStatement]:
        """
        Get financial statements for a company.

        Args:
            ticker: Stock ticker symbol
            statement_type: balance_sheet, income_statement, or cash_flow
            periods: Number of periods to retrieve

        Returns:
            List of FinancialStatement models
        """
        cache_key = f"financials:{ticker.upper()}:{statement_type}:{periods}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return [FinancialStatement.model_validate(f) for f in cached]

        logger.debug(f"Fetching {statement_type} for {ticker}")
        edgar_company: EdgarCompany = self._rate_limited_call(
            EdgarCompany, ticker.upper()
        )

        # Get the most recent 10-K or 10-Q filings
        filings = edgar_company.get_filings(form="10-K").head(periods)

        statements = []
        for filing in filings:
            try:
                # edgartools provides financials via the filing object
                tenk = filing.obj()
                if not hasattr(tenk, "financials"):
                    continue

                financials = tenk.financials

                if statement_type == "balance_sheet" and hasattr(financials, "balance_sheet"):
                    data = financials.balance_sheet.to_dict() if hasattr(financials.balance_sheet, "to_dict") else {}
                elif statement_type == "income_statement" and hasattr(financials, "income_statement"):
                    data = financials.income_statement.to_dict() if hasattr(financials.income_statement, "to_dict") else {}
                elif statement_type == "cash_flow" and hasattr(financials, "cash_flow_statement"):
                    data = financials.cash_flow_statement.to_dict() if hasattr(financials.cash_flow_statement, "to_dict") else {}
                else:
                    continue

                statement = FinancialStatement(
                    statement_type=statement_type,
                    period_end=filing.filing_date,
                    fiscal_year=filing.filing_date.year,
                    fiscal_period="FY",
                    data=data,
                )
                statements.append(statement)
            except Exception as e:
                logger.warning(f"Failed to extract financials from {filing.accession_number}: {e}")
                continue

        self.cache.set(cache_key, [s.model_dump(mode="json") for s in statements])
        return statements

    def get_insider_transactions(
        self,
        ticker: str,
        limit: int = 20,
    ) -> list[InsiderTransaction]:
        """
        Get insider transactions (Form 4) for a company.

        Args:
            ticker: Stock ticker symbol
            limit: Maximum number of transactions

        Returns:
            List of InsiderTransaction models
        """
        cache_key = f"insider:{ticker.upper()}:{limit}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return [InsiderTransaction.model_validate(t) for t in cached]

        logger.debug(f"Fetching Form 4 filings for {ticker}")
        company = self.get_company(ticker)

        edgar_company: EdgarCompany = self._rate_limited_call(
            EdgarCompany, ticker.upper()
        )
        form4_filings = edgar_company.get_filings(form="4").head(limit)

        transactions = []
        for filing in form4_filings:
            try:
                form4 = filing.obj()
                if not hasattr(form4, "transactions"):
                    continue

                for txn in form4.transactions:
                    transaction = InsiderTransaction(
                        accession_number=filing.accession_number,
                        filing_date=filing.filing_date,
                        company=company,
                        insider_name=getattr(form4, "owner_name", "Unknown"),
                        insider_title=getattr(form4, "owner_title", None),
                        transaction_date=getattr(txn, "transaction_date", filing.filing_date),
                        transaction_type=getattr(txn, "transaction_code", "U"),
                        shares=float(getattr(txn, "shares", 0)),
                        price_per_share=float(getattr(txn, "price_per_share", 0)) if getattr(txn, "price_per_share", None) else None,
                        total_value=None,
                        shares_owned_after=float(getattr(txn, "shares_owned_following", 0)) if getattr(txn, "shares_owned_following", None) else None,
                    )
                    transactions.append(transaction)
            except Exception as e:
                logger.warning(f"Failed to parse Form 4 {filing.accession_number}: {e}")
                continue

        self.cache.set(cache_key, [t.model_dump(mode="json") for t in transactions])
        return transactions

    def search_filings(
        self,
        query: str,
        form_types: list[str] | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 20,
    ) -> list[Filing]:
        """
        Search filings by keyword using SEC's EFTS (EDGAR Full-Text Search) API.

        This searches the full text of all EDGAR filings submitted since 2001,
        including all attachments (exhibits).

        Args:
            query: Search query (supports boolean operators: AND, OR, NOT, "exact phrase")
            form_types: List of form types to filter (e.g., ["10-K", "10-Q"])
            start_date: Filter filings after this date
            end_date: Filter filings before this date
            limit: Maximum number of filings to return (max 100)

        Returns:
            List of Filing models matching the search criteria

        Examples:
            >>> client.search_filings("artificial intelligence", form_types=["10-K"])
            >>> client.search_filings('"risk factors" cybersecurity', start_date=date(2024, 1, 1))
        """
        self.rate_limiter.wait()

        # Build query parameters
        params: dict[str, str] = {"q": query}

        # Date range
        if start_date or end_date:
            params["dateRange"] = "custom"
            if start_date:
                params["startdt"] = start_date.isoformat()
            if end_date:
                params["enddt"] = end_date.isoformat()

        # Form types - EFTS accepts comma-separated list
        if form_types:
            params["forms"] = ",".join(form_types)

        try:
            logger.debug(f"EFTS search: query={query}, forms={form_types}, date_range={start_date}-{end_date}")

            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    EFTS_SEARCH_URL,
                    params=params,
                    headers={"User-Agent": settings.sec_user_agent},
                )
                response.raise_for_status()
                data = response.json()

            hits = data.get("hits", {}).get("hits", [])
            total = data.get("hits", {}).get("total", {}).get("value", 0)
            logger.info(f"EFTS search found {total} results for query: {query}")

            # Convert EFTS results to Filing models
            filings: list[Filing] = []
            seen_accessions: set[str] = set()  # Deduplicate by accession number

            for hit in hits[:limit * 2]:  # Fetch extra to account for duplicates
                if len(filings) >= limit:
                    break

                source = hit.get("_source", {})

                # Get accession number (EFTS uses 'adsh' without dashes)
                adsh = source.get("adsh", "")
                if not adsh or adsh in seen_accessions:
                    continue
                seen_accessions.add(adsh)

                # Convert adsh format (000032019324000123) to standard format (0000320193-24-000123)
                accession_number = self._format_accession_number(adsh)

                # Extract company info from display_names
                display_names = source.get("display_names", [])
                ticker = ""
                company_name = ""
                cik = ""

                if display_names:
                    # Format: "Apple Inc.  (AAPL)  (CIK 0000320193)"
                    match = re.search(r"(.+?)\s+\(([A-Z]+)\)\s+\(CIK\s+(\d+)\)", display_names[0])
                    if match:
                        company_name = match.group(1).strip()
                        ticker = match.group(2)
                        cik = match.group(3)
                    else:
                        company_name = display_names[0]

                # Get CIK from ciks array if not found in display_names
                if not cik and source.get("ciks"):
                    cik = source["ciks"][0].lstrip("0") or "0"

                # Parse filing date
                file_date_str = source.get("file_date", "")
                try:
                    filing_date = date.fromisoformat(file_date_str) if file_date_str else date.today()
                except ValueError:
                    filing_date = date.today()

                # Parse period end date
                period_ending_str = source.get("period_ending", "")
                try:
                    report_date = date.fromisoformat(period_ending_str) if period_ending_str else None
                except ValueError:
                    report_date = None

                # Get form type (prefer root_forms for main form, file_type might be exhibit)
                form_type = source.get("form", "")
                root_forms = source.get("root_forms", [])
                if root_forms and not form_type:
                    form_type = root_forms[0]

                # Get SIC code
                sics = source.get("sics", [])
                sic = sics[0] if sics else None

                # Create Company model
                company = Company(
                    cik=cik or "0",
                    ticker=ticker or "UNKNOWN",
                    name=company_name or "Unknown Company",
                    sic=sic,
                    sic_description=None,  # Not provided by EFTS
                    exchange=None,  # Not provided by EFTS
                )

                # Generate SEC URL
                url = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{adsh}/"

                filing = Filing(
                    accession_number=accession_number,
                    form_type=form_type,
                    filing_date=filing_date,
                    report_date=report_date,
                    company=company,
                    primary_document=source.get("file_description"),
                    url=url,
                )
                filings.append(filing)

            return filings

        except httpx.HTTPError as e:
            logger.error(f"EFTS search HTTP error: {e}")
            return []
        except Exception as e:
            logger.error(f"EFTS search failed: {e}")
            return []

    def _format_accession_number(self, adsh: str) -> str:
        """
        Convert EFTS adsh format to standard accession number format.

        EFTS format: 000032019324000123 (18 digits, no dashes)
        Standard format: 0000320193-24-000123 (10-2-6 with dashes)
        """
        if len(adsh) != 18:
            return adsh
        return f"{adsh[:10]}-{adsh[10:12]}-{adsh[12:]}"


# Global client instance
_client: EdgarClient | None = None


def get_edgar_client() -> EdgarClient:
    """Get or create the global Edgar client."""
    global _client
    if _client is None:
        _client = EdgarClient()
    return _client
