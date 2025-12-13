"""SEC API for LLMs - Python SDK

A developer-friendly client for accessing LLM-ready SEC filing data.

Example:
    >>> from sec_api_llm import SecClient
    >>> client = SecClient()
    >>> table = client.tables.parse(ticker="AAPL", table="income_statement", form="10-K", year=2024)
    >>> print(table.markdown)
    >>> print(table.citation)
"""

from .client import SecClient
from .exceptions import AuthenticationError, NotFoundError, ParsingError, SecApiError
from .models import Filing, ParsedTable, SearchResponse, SearchResult

__version__ = "0.1.0"

__all__ = [
    "SecClient",
    "SecApiError",
    "AuthenticationError",
    "NotFoundError",
    "ParsingError",
    "ParsedTable",
    "Filing",
    "SearchResponse",
    "SearchResult",
]
