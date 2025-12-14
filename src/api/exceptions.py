"""API-specific exception hierarchy used by the FastAPI layer."""

class SecApiError(Exception):
    """Base exception for SEC API errors."""
    def __init__(self, message: str, status_code: int = 500):
        """Store error message and HTTP status for responses."""
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class TableNotFound(SecApiError):
    """Raised when a requested table cannot be found."""
    def __init__(self, table_name: str, ticker: str):
        """Record which table and ticker could not be located."""
        super().__init__(f"Table '{table_name}' not found for {ticker}", status_code=404)

class FilingNotFound(SecApiError):
    """Raised when a requested filing cannot be found."""
    def __init__(self, ticker: str, form_type: str, year: int | None = None):
        """Construct a message describing which filing is missing."""
        msg = f"No {form_type} filing found for {ticker}"
        if year:
            msg += f" in {year}"
        super().__init__(msg, status_code=404)

class ParsingError(SecApiError):
    """Raised when table parsing fails."""
    def __init__(self, detail: str):
        """Include parsing details in the exception message."""
        super().__init__(f"Parsing failed: {detail}", status_code=422)
