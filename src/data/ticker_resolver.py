"""Ticker resolution for converting company names to ticker symbols."""

import logging
from difflib import SequenceMatcher
from functools import lru_cache
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Comprehensive mapping of company names/variations to tickers
# Covers S&P 500 + popular companies
COMPANY_TICKERS: dict[str, str] = {
    # Technology
    "apple": "AAPL",
    "apple inc": "AAPL",
    "microsoft": "MSFT",
    "microsoft corporation": "MSFT",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "alphabet inc": "GOOGL",
    "amazon": "AMZN",
    "amazon.com": "AMZN",
    "amazon com": "AMZN",
    "nvidia": "NVDA",
    "nvidia corporation": "NVDA",
    "meta": "META",
    "meta platforms": "META",
    "facebook": "META",
    "tesla": "TSLA",
    "tesla inc": "TSLA",
    "tesla motors": "TSLA",
    "intel": "INTC",
    "intel corporation": "INTC",
    "amd": "AMD",
    "advanced micro devices": "AMD",
    "broadcom": "AVGO",
    "qualcomm": "QCOM",
    "adobe": "ADBE",
    "adobe inc": "ADBE",
    "salesforce": "CRM",
    "salesforce.com": "CRM",
    "oracle": "ORCL",
    "oracle corporation": "ORCL",
    "ibm": "IBM",
    "cisco": "CSCO",
    "cisco systems": "CSCO",
    "netflix": "NFLX",
    "paypal": "PYPL",
    "paypal holdings": "PYPL",
    "intuit": "INTU",
    "servicenow": "NOW",
    "texas instruments": "TXN",
    "uber": "UBER",
    "uber technologies": "UBER",
    "airbnb": "ABNB",
    "zoom": "ZM",
    "zoom video": "ZM",
    "snowflake": "SNOW",
    "palantir": "PLTR",
    "palantir technologies": "PLTR",
    "block": "SQ",
    "square": "SQ",
    "shopify": "SHOP",
    "twilio": "TWLO",
    "crowdstrike": "CRWD",
    "datadog": "DDOG",
    "mongodb": "MDB",
    "splunk": "SPLK",
    "docusign": "DOCU",
    "okta": "OKTA",
    "zscaler": "ZS",
    "palo alto networks": "PANW",
    "fortinet": "FTNT",

    # Finance
    "jpmorgan": "JPM",
    "jp morgan": "JPM",
    "jpmorgan chase": "JPM",
    "bank of america": "BAC",
    "bofa": "BAC",
    "wells fargo": "WFC",
    "citigroup": "C",
    "citi": "C",
    "goldman sachs": "GS",
    "morgan stanley": "MS",
    "blackrock": "BLK",
    "visa": "V",
    "mastercard": "MA",
    "american express": "AXP",
    "amex": "AXP",
    "charles schwab": "SCHW",
    "schwab": "SCHW",
    "capital one": "COF",
    "pnc": "PNC",
    "us bank": "USB",
    "truist": "TFC",
    "state street": "STT",
    "blackstone": "BX",
    "kkr": "KKR",
    "apollo": "APO",

    # Healthcare & Pharma
    "johnson & johnson": "JNJ",
    "j&j": "JNJ",
    "johnson and johnson": "JNJ",
    "pfizer": "PFE",
    "merck": "MRK",
    "abbvie": "ABBV",
    "eli lilly": "LLY",
    "lilly": "LLY",
    "bristol myers squibb": "BMY",
    "amgen": "AMGN",
    "gilead": "GILD",
    "gilead sciences": "GILD",
    "regeneron": "REGN",
    "biogen": "BIIB",
    "vertex": "VRTX",
    "vertex pharmaceuticals": "VRTX",
    "moderna": "MRNA",
    "unitedhealth": "UNH",
    "unitedhealth group": "UNH",
    "cvs": "CVS",
    "cvs health": "CVS",
    "anthem": "ELV",
    "elevance health": "ELV",
    "cigna": "CI",
    "humana": "HUM",
    "medtronic": "MDT",
    "abbott": "ABT",
    "abbott laboratories": "ABT",
    "stryker": "SYK",
    "boston scientific": "BSX",
    "thermo fisher": "TMO",
    "thermo fisher scientific": "TMO",
    "danaher": "DHR",
    "becton dickinson": "BDX",

    # Retail & Consumer
    "walmart": "WMT",
    "amazon": "AMZN",
    "costco": "COST",
    "home depot": "HD",
    "the home depot": "HD",
    "lowes": "LOW",
    "lowe's": "LOW",
    "target": "TGT",
    "dollar general": "DG",
    "dollar tree": "DLTR",
    "tjx": "TJX",
    "tj maxx": "TJX",
    "ross stores": "ROST",
    "nike": "NKE",
    "starbucks": "SBUX",
    "mcdonalds": "MCD",
    "mcdonald's": "MCD",
    "chipotle": "CMG",
    "yum brands": "YUM",
    "coca cola": "KO",
    "coca-cola": "KO",
    "pepsi": "PEP",
    "pepsico": "PEP",
    "procter & gamble": "PG",
    "procter and gamble": "PG",
    "p&g": "PG",
    "colgate palmolive": "CL",
    "colgate-palmolive": "CL",
    "estee lauder": "EL",
    "philip morris": "PM",
    "altria": "MO",
    "mondelez": "MDLZ",
    "general mills": "GIS",
    "kellogg": "K",
    "kellogg's": "K",
    "kraft heinz": "KHC",
    "hershey": "HSY",
    "clorox": "CLX",

    # Energy
    "exxon": "XOM",
    "exxon mobil": "XOM",
    "exxonmobil": "XOM",
    "chevron": "CVX",
    "conocophillips": "COP",
    "conoco phillips": "COP",
    "occidental": "OXY",
    "occidental petroleum": "OXY",
    "eog resources": "EOG",
    "pioneer natural resources": "PXD",
    "schlumberger": "SLB",
    "halliburton": "HAL",
    "marathon petroleum": "MPC",
    "valero": "VLO",
    "phillips 66": "PSX",

    # Industrial & Aerospace
    "boeing": "BA",
    "the boeing company": "BA",
    "lockheed martin": "LMT",
    "raytheon": "RTX",
    "northrop grumman": "NOC",
    "general dynamics": "GD",
    "general electric": "GE",
    "ge": "GE",
    "honeywell": "HON",
    "3m": "MMM",
    "caterpillar": "CAT",
    "deere": "DE",
    "john deere": "DE",
    "union pacific": "UNP",
    "csx": "CSX",
    "norfolk southern": "NSC",
    "ups": "UPS",
    "united parcel service": "UPS",
    "fedex": "FDX",

    # Automotive
    "ford": "F",
    "ford motor": "F",
    "general motors": "GM",
    "gm": "GM",
    "rivian": "RIVN",
    "lucid": "LCID",
    "lucid motors": "LCID",
    "nio": "NIO",

    # Entertainment & Media
    "disney": "DIS",
    "walt disney": "DIS",
    "the walt disney company": "DIS",
    "comcast": "CMCSA",
    "warner bros discovery": "WBD",
    "warner bros": "WBD",
    "paramount": "PARA",
    "fox": "FOXA",
    "fox corporation": "FOXA",
    "spotify": "SPOT",
    "roblox": "RBLX",
    "activision": "ATVI",
    "activision blizzard": "ATVI",
    "electronic arts": "EA",
    "ea": "EA",
    "take two": "TTWO",
    "take-two": "TTWO",

    # Telecom
    "at&t": "T",
    "att": "T",
    "verizon": "VZ",
    "t-mobile": "TMUS",
    "tmobile": "TMUS",

    # Real Estate & Construction
    "prologis": "PLD",
    "american tower": "AMT",
    "crown castle": "CCI",
    "equinix": "EQIX",
    "digital realty": "DLR",
    "public storage": "PSA",
    "simon property group": "SPG",
    "realty income": "O",
    "weyerhaeuser": "WY",
    "lennar": "LEN",
    "dr horton": "DHI",
    "d.r. horton": "DHI",
    "pulte": "PHM",
    "pultegroup": "PHM",

    # Other notable companies
    "berkshire hathaway": "BRK.B",
    "berkshire": "BRK.B",
    "accenture": "ACN",
    "deloitte": "ACN",  # Closest public equivalent
    "automatic data processing": "ADP",
    "adp": "ADP",
    "paychex": "PAYX",
    "fidelity national": "FIS",
    "fiserv": "FI",
    "global payments": "GPN",
    "s&p global": "SPGI",
    "moody's": "MCO",
    "moodys": "MCO",
    "msci": "MSCI",
    "intercontinental exchange": "ICE",
    "ice": "ICE",
    "cme group": "CME",
    "nasdaq": "NDAQ",
    "autodesk": "ADSK",
    "ansys": "ANSS",
    "cadence": "CDNS",
    "synopsys": "SNPS",
    "veeva": "VEEV",
    "workday": "WDAY",
    "coupa": "COUP",
    "zoom info": "ZI",
    "zoominfo": "ZI",
}


class TickerResolver:
    """Resolves company names to ticker symbols."""

    def __init__(self, sec_api_enabled: bool = True):
        """
        Initialize the resolver.

        Args:
            sec_api_enabled: Whether to use SEC EDGAR API as fallback
        """
        self.sec_api_enabled = sec_api_enabled
        self._sec_cache: dict[str, str] = {}

    def resolve(self, query: str) -> str | None:
        """
        Resolve a company name or ticker to a valid ticker symbol.

        Args:
            query: Company name or ticker symbol

        Returns:
            Ticker symbol if found, None otherwise
        """
        if not query or not query.strip():
            return None

        query = query.strip()
        query_upper = query.upper()
        query_lower = query.lower()

        # 1. Check if it's already a valid ticker (uppercase, 1-5 chars)
        if query_upper.isalpha() and 1 <= len(query_upper) <= 5:
            # Could be a ticker - check if it's in our known list
            if query_upper in COMPANY_TICKERS.values():
                return query_upper

        # 2. Try exact match in company names
        if query_lower in COMPANY_TICKERS:
            return COMPANY_TICKERS[query_lower]

        # 3. Try fuzzy matching
        fuzzy_match = self._fuzzy_match(query_lower)
        if fuzzy_match:
            return fuzzy_match

        # 4. Try SEC EDGAR API as fallback
        if self.sec_api_enabled:
            sec_result = self._search_sec_edgar(query)
            if sec_result:
                return sec_result

        # 5. If all else fails, assume it might be a ticker
        if query_upper.isalpha() and 1 <= len(query_upper) <= 5:
            return query_upper

        return None

    def _fuzzy_match(self, query: str, threshold: float = 0.6) -> str | None:
        """
        Find best fuzzy match for a company name.

        Args:
            query: Company name to search for
            threshold: Minimum similarity score (0-1)

        Returns:
            Ticker if a good match is found, None otherwise
        """
        best_match = None
        best_score = 0.0

        for company_name, ticker in COMPANY_TICKERS.items():
            # Calculate similarity
            score = SequenceMatcher(None, query, company_name).ratio()

            # Also try matching against the ticker itself (case-insensitive)
            ticker_score = SequenceMatcher(None, query.upper(), ticker).ratio()
            score = max(score, ticker_score)

            if score > best_score and score >= threshold:
                best_score = score
                best_match = ticker

        return best_match

    @lru_cache(maxsize=500)
    def _search_sec_edgar(self, query: str) -> str | None:
        """
        Search SEC EDGAR company search API.

        Args:
            query: Company name to search for

        Returns:
            Ticker if found, None otherwise
        """
        try:
            # SEC EDGAR company search endpoint
            url = f"https://efts.sec.gov/LATEST/search-index?q={query}&dateRange=custom&startdt=2020-01-01&enddt=2025-12-31&forms=10-K"

            headers = {
                "User-Agent": "SEC-EDGAR-Agent/1.0 (research@example.com)",
                "Accept": "application/json",
            }

            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    hits = data.get("hits", {}).get("hits", [])

                    if hits:
                        # Get the first result's ticker
                        first_hit = hits[0].get("_source", {})
                        tickers = first_hit.get("tickers", [])
                        if tickers:
                            return tickers[0].upper()

        except Exception as e:
            logger.warning(f"SEC EDGAR search failed: {e}")

        return None

    def get_suggestions(self, query: str, limit: int = 5) -> list[dict[str, str]]:
        """
        Get ticker suggestions for a partial query.

        Args:
            query: Partial company name or ticker
            limit: Maximum number of suggestions

        Returns:
            List of {ticker, name} dictionaries
        """
        if not query or len(query) < 2:
            return []

        query_lower = query.lower()
        results: list[tuple[float, str, str]] = []

        for company_name, ticker in COMPANY_TICKERS.items():
            # Check if query is prefix of company name or ticker
            if company_name.startswith(query_lower) or ticker.lower().startswith(query_lower):
                score = 1.0 if company_name.startswith(query_lower) else 0.9
                results.append((score, ticker, company_name.title()))
            else:
                # Fuzzy match
                score = SequenceMatcher(None, query_lower, company_name).ratio()
                if score >= 0.5:
                    results.append((score, ticker, company_name.title()))

        # Sort by score descending, then alphabetically
        results.sort(key=lambda x: (-x[0], x[1]))

        # Deduplicate by ticker
        seen_tickers: set[str] = set()
        suggestions: list[dict[str, str]] = []

        for _, ticker, name in results:
            if ticker not in seen_tickers:
                seen_tickers.add(ticker)
                suggestions.append({"ticker": ticker, "name": name})
                if len(suggestions) >= limit:
                    break

        return suggestions


# Module-level singleton
_resolver: TickerResolver | None = None


def get_ticker_resolver() -> TickerResolver:
    """Get or create the global ticker resolver instance."""
    global _resolver
    if _resolver is None:
        _resolver = TickerResolver()
    return _resolver


def resolve_ticker(query: str) -> str | None:
    """
    Convenience function to resolve a company name to ticker.

    Args:
        query: Company name or ticker

    Returns:
        Ticker symbol if found, None otherwise
    """
    return get_ticker_resolver().resolve(query)
