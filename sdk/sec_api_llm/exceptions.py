class SecApiError(Exception):
    """Base exception for SEC API errors."""
    pass

class AuthenticationError(SecApiError):
    """Raised when authentication fails."""
    pass

class NotFoundError(SecApiError):
    """Raised when a resource is not found."""
    pass

class ParsingError(SecApiError):
    """Raised when table parsing fails."""
    pass
