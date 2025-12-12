"""SEC EDGAR Agent tools.

Import this module to register all tools with the registry.
"""

# Import tool modules to trigger registration
from src.tools import analysis, fetch, financials, search, semantic, watchlist
from src.tools.registry import registry

__all__ = [
    "registry",
    "analysis",
    "fetch",
    "financials",
    "search",
    "semantic",
    "watchlist",
]
