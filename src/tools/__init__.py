"""SEC EDGAR Agent tools.

Import this module to register all tools with the registry.
"""

from src.tools.registry import registry

# Import tool modules to trigger registration
from src.tools import analysis, fetch, financials, search, semantic, watchlist

__all__ = [
    "registry",
    "analysis",
    "fetch",
    "financials",
    "search",
    "semantic",
    "watchlist",
]
