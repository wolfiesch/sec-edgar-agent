"""SEC EDGAR Agent tools.

Import this module to register all tools with the registry.
"""

from src.tools.registry import registry

# Import tool modules to trigger registration
from src.tools import fetch, financials, search

__all__ = ["registry", "fetch", "financials", "search"]
