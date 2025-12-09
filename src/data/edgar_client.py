"""SEC EDGAR API client wrapper using edgartools."""

import logging
from datetime import date
from typing import Any

import edgar
from edgar import Company as EdgarCompany
from edgar import Filing as EdgarFiling

from src.config import settings
from src.data.cache import get_cache
from src.data.models import Company, Filing, FinancialStatement, InsiderTransaction
from src.utils.rate_limiter import get_rate_limiter

logger = logging.getLogger(__name__)


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
        Search filings by keyword.

        Note: This uses SEC's full-text search API.
        """
        # [*TO-DO*] - Implement full-text search using SEC's EFTS API
        # For now, this is a placeholder
        logger.warning("Full-text search not yet implemented")
        return []


# Global client instance
_client: EdgarClient | None = None


def get_edgar_client() -> EdgarClient:
    """Get or create the global Edgar client."""
    global _client
    if _client is None:
        _client = EdgarClient()
    return _client
