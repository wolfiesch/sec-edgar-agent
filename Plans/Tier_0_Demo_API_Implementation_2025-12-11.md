# Tier 0 Implementation Plan: Demo-able MVP Core

**Created:** 12/11/2025 04:53 AM PST (via pst-timestamp)
**Timeline:** 2-3 days (16-24 hours focused work)
**Goal:** Build working API demo for user validation interviews
**Status:** Ready to implement

---

## Overview

Build a minimal but **demo-able** API that showcases our three core differentiators:
1. ✅ **Structured table parsing** (100% accuracy - already validated)
2. ✅ **Citation system** (traceable responses)
3. ✅ **Python SDK** (developer-first experience)

This Tier 0 MVP enables high-quality user interviews with a **working product demo** instead of mockups or slides.

---

## Success Criteria

At the end of Tier 0, we can demonstrate:

| Capability | Demo Action | Expected Result |
|------------|-------------|-----------------|
| **Table parsing** | `curl POST /api/v1/tables/parse` with AAPL 10-K | Returns Markdown table with 100% accuracy |
| **Citation** | Every API response includes citation | `[AAPL 10-K 2024, Item 8, Page 45]` format |
| **Python SDK** | `pip install -e .` → import and use | `client.tables.parse(ticker="AAPL")` works |
| **Live demo** | Share localhost or deployed URL in interview | User can make API calls during conversation |

**Go/No-Go:** If we can't demo these 3 capabilities, Tier 0 is incomplete.

---

## Architecture Overview

### High-Level Structure

```
┌─────────────────────────────────────────────────────────────┐
│                        User / SDK                            │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   /filings   │  │   /tables    │  │   /search    │      │
│  │   endpoints  │  │   endpoints  │  │   endpoints  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└───────────────────────────┬─────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │ EdgarClient  │ │ TableParser  │ │ Citations    │
    │ (existing)   │ │ (from POC)   │ │ (new)        │
    └──────────────┘ └──────────────┘ └──────────────┘
            │
            ▼
    ┌──────────────┐
    │  SEC EDGAR   │
    │  data.sec.gov│
    └──────────────┘
```

### Directory Structure (After Tier 0)

```
sec-edgar-agent/
├── src/
│   ├── api/                        # NEW - FastAPI app
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app initialization
│   │   ├── dependencies.py         # Shared dependencies (auth, etc.)
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── health.py           # GET /health
│   │   │   ├── filings.py          # GET /filings/{ticker}/{form}
│   │   │   └── tables.py           # POST /tables/parse
│   │   └── models/
│   │       ├── __init__.py
│   │       ├── requests.py         # Pydantic request models
│   │       └── responses.py        # Pydantic response models
│   ├── parsers/                    # NEW - Move POC here
│   │   ├── __init__.py
│   │   ├── table_parser.py         # From POC, refactored
│   │   └── inline_xbrl.py          # XBRL extraction logic
│   ├── utils/
│   │   ├── citations.py            # NEW - Citation system
│   │   └── formatting.py           # NEW - Markdown/JSON formatters
│   ├── data/
│   │   ├── edgar_client.py         # EXISTING (use as-is)
│   │   └── cache.py                # NEW - Simple file cache
│   └── agents/                     # EXISTING (ignore for Tier 0)
├── sdk/                            # NEW - Python SDK package
│   ├── sec_api_llm/
│   │   ├── __init__.py
│   │   ├── client.py               # Main SecClient class
│   │   ├── resources/
│   │   │   ├── __init__.py
│   │   │   ├── filings.py          # FilingsResource
│   │   │   └── tables.py           # TablesResource
│   │   ├── models.py               # Response models
│   │   └── exceptions.py           # Custom exceptions
│   ├── pyproject.toml              # SDK package config
│   └── README.md                   # SDK documentation
├── tests/
│   └── api/                        # NEW - API tests
│       ├── test_health.py
│       ├── test_tables.py
│       └── test_filings.py
└── scripts/
    └── table_parsing_poc/          # EXISTING (keep for reference)
```

---

## Day-by-Day Implementation Plan

### **Day 1: FastAPI Foundation + Table Parsing Endpoint** (8-12 hours)

**Goal:** Get to "hello world" API with working table parsing

#### Morning Session (4-6 hours): FastAPI Setup

**Tasks:**

1. **Create API package structure** (30 min)
   ```bash
   mkdir -p src/api/routes src/api/models
   touch src/api/{__init__.py,main.py,dependencies.py}
   touch src/api/routes/{__init__.py,health.py,filings.py,tables.py}
   touch src/api/models/{__init__.py,requests.py,responses.py}
   ```

2. **Install dependencies** (15 min)
   ```bash
   # Add to pyproject.toml
   uv add fastapi uvicorn[standard] pydantic pydantic-settings
   ```

3. **Create FastAPI app skeleton** (1 hour)

   **File:** `src/api/main.py`
   ```python
   from fastapi import FastAPI
   from fastapi.middleware.cors import CORSMiddleware

   from .routes import health, filings, tables

   app = FastAPI(
       title="SEC API for LLMs",
       description="LLM-ready SEC filing data with structured tables and citations",
       version="0.1.0",
       docs_url="/docs",
       redoc_url="/redoc",
   )

   # CORS for demo purposes (restrict in production)
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],
       allow_methods=["*"],
       allow_headers=["*"],
   )

   # Include routers
   app.include_router(health.router, tags=["health"])
   app.include_router(filings.router, prefix="/api/v1/filings", tags=["filings"])
   app.include_router(tables.router, prefix="/api/v1/tables", tags=["tables"])

   @app.get("/")
   async def root():
       return {
           "message": "SEC API for LLMs",
           "docs": "/docs",
           "version": "0.1.0"
       }
   ```

4. **Create health check endpoint** (30 min)

   **File:** `src/api/routes/health.py`
   ```python
   from fastapi import APIRouter

   router = APIRouter()

   @router.get("/health")
   async def health_check():
       """Health check endpoint for monitoring."""
       return {
           "status": "healthy",
           "service": "sec-api-llm",
           "version": "0.1.0"
       }
   ```

5. **Test FastAPI runs** (30 min)
   ```bash
   # Run development server
   uv run uvicorn src.api.main:app --reload --port 8000

   # Test in browser
   open http://localhost:8000/docs

   # Test with curl
   curl http://localhost:8000/health
   ```

**Checkpoint 1:** ✅ FastAPI app runs, /health returns 200, Swagger docs load

---

#### Afternoon Session (4-6 hours): Table Parsing Integration

**Tasks:**

6. **Move POC code to production** (1 hour)
   ```bash
   mkdir -p src/parsers
   cp scripts/table_parsing_poc/parse_inline_xbrl.py src/parsers/table_parser.py
   ```

   **Refactor to class-based:**
   ```python
   # src/parsers/table_parser.py
   from dataclasses import dataclass
   from pathlib import Path
   import pandas as pd
   from bs4 import BeautifulSoup

   @dataclass
   class ParsedTable:
       """Structured table with metadata."""
       markdown: str
       structured: list[dict]
       citation: str
       confidence: str  # "high", "medium", "low"
       source_method: str  # "inline-xbrl"

   class TableParser:
       """Production table parser using inline XBRL extraction."""

       def __init__(self):
           self.context_to_region = {
               "c-149": "Americas",
               "c-150": "Europe",
               "c-151": "Greater China",
               "c-152": "Japan",
               "c-153": "Rest of Asia Pacific",
               "c-154": "Corporate",
               "c-1": "Total",
           }

       def parse_from_html(self, html_content: str, filing_info: dict) -> ParsedTable:
           """Parse table from HTML using inline XBRL tags."""
           # ... (existing POC logic, refactored)
           pass

       def parse_from_filing(
           self,
           ticker: str,
           form_type: str,
           table_identifier: str
       ) -> ParsedTable:
           """High-level interface: fetch filing and parse table."""
           # 1. Fetch filing using EdgarClient
           # 2. Identify table by name/keywords
           # 3. Extract table HTML
           # 4. Parse using parse_from_html()
           pass
   ```

7. **Create Pydantic models** (1 hour)

   **File:** `src/api/models/requests.py`
   ```python
   from pydantic import BaseModel, Field

   class TableParseRequest(BaseModel):
       """Request to parse a specific table from a filing."""
       ticker: str = Field(..., example="AAPL", description="Stock ticker symbol")
       form_type: str = Field(..., example="10-K", description="SEC form type")
       year: int = Field(..., example=2024, ge=2000, le=2030)
       table_name: str = Field(
           ...,
           example="segment_information",
           description="Table identifier (e.g., 'segment_information', 'lease_maturity')"
       )
   ```

   **File:** `src/api/models/responses.py`
   ```python
   from pydantic import BaseModel
   from typing import Optional

   class Citation(BaseModel):
       """Source citation for data."""
       ticker: str
       form_type: str
       filing_date: str
       section: str
       page: Optional[int] = None

       def to_string(self) -> str:
           """Format as [TICKER FORM YEAR, Section, Page]"""
           parts = [f"{self.ticker} {self.form_type} {self.filing_date[:4]}"]
           if self.section:
               parts.append(self.section)
           if self.page:
               parts.append(f"Page {self.page}")
           return f"[{', '.join(parts)}]"

   class ParsedTableResponse(BaseModel):
       """Response containing parsed table data."""
       markdown: str
       structured: list[dict]
       citation: str
       confidence: str
       metadata: dict
   ```

8. **Implement /tables/parse endpoint** (2 hours)

   **File:** `src/api/routes/tables.py`
   ```python
   from fastapi import APIRouter, HTTPException
   from ...parsers.table_parser import TableParser
   from ..models.requests import TableParseRequest
   from ..models.responses import ParsedTableResponse

   router = APIRouter()
   parser = TableParser()  # Singleton for demo

   @router.post("/parse", response_model=ParsedTableResponse)
   async def parse_table(request: TableParseRequest):
       """
       Parse a table from SEC filing with 100% accuracy.

       Returns structured Markdown table ready for LLM consumption.
       """
       try:
           result = parser.parse_from_filing(
               ticker=request.ticker,
               form_type=request.form_type,
               table_identifier=request.table_name
           )

           return ParsedTableResponse(
               markdown=result.markdown,
               structured=result.structured,
               citation=result.citation,
               confidence=result.confidence,
               metadata={
                   "source_method": result.source_method,
                   "ticker": request.ticker,
                   "form_type": request.form_type,
                   "year": request.year
               }
           )
       except Exception as e:
           raise HTTPException(
               status_code=500,
               detail=f"Failed to parse table: {str(e)}"
           )
   ```

9. **Test table parsing endpoint** (1 hour)
   ```bash
   # Start server
   uv run uvicorn src.api.main:app --reload

   # Test with curl
   curl -X POST http://localhost:8000/api/v1/tables/parse \
     -H "Content-Type: application/json" \
     -d '{
       "ticker": "AAPL",
       "form_type": "10-K",
       "year": 2024,
       "table_name": "segment_information"
     }' | jq

   # Expected: Markdown table with citation
   ```

**Checkpoint 2:** ✅ Table parsing endpoint works, returns structured data with citation

---

### **Day 2: Citation System + Filings Endpoint** (6-8 hours)

**Goal:** Complete API with citations and basic filing retrieval

#### Morning Session (3-4 hours): Citation System

**Tasks:**

10. **Create citation utility** (1.5 hours)

    **File:** `src/utils/citations.py`
    ```python
    from dataclasses import dataclass
    from typing import Optional
    import edgar

    @dataclass
    class Citation:
        """Source citation for SEC filing data."""
        ticker: str
        form_type: str
        filing_date: str
        accession_no: str
        section: Optional[str] = None
        page: Optional[int] = None
        source_url: Optional[str] = None

        def to_string(self) -> str:
            """
            Format citation as [TICKER FORM YEAR, Section, Page].

            Examples:
                [AAPL 10-K 2024, Item 8, Page 45]
                [MSFT 10-Q 2024, Item 2]
                [NVDA 8-K 2024]
            """
            year = self.filing_date[:4] if self.filing_date else ""
            parts = [f"{self.ticker} {self.form_type} {year}"]

            if self.section:
                parts.append(self.section)
            if self.page:
                parts.append(f"Page {self.page}")

            return f"[{', '.join(parts)}]"

        def to_dict(self) -> dict:
            """Convert to dictionary for API response."""
            return {
                "citation": self.to_string(),
                "source_url": self.source_url or self._generate_sec_url(),
                "ticker": self.ticker,
                "form_type": self.form_type,
                "filing_date": self.filing_date,
                "section": self.section,
                "page": self.page
            }

        def _generate_sec_url(self) -> str:
            """Generate SEC.gov URL for filing."""
            if not self.accession_no:
                return None
            # Format: https://www.sec.gov/cgi-bin/viewer?action=view&cik=...&accession_number=...
            acc = self.accession_no.replace("-", "")
            return f"https://www.sec.gov/cgi-bin/viewer?action=view&accession_number={self.accession_no}"

    def create_citation_from_filing(
        filing: edgar.Filing,
        section: Optional[str] = None,
        page: Optional[int] = None
    ) -> Citation:
        """Helper to create citation from edgar.Filing object."""
        return Citation(
            ticker=filing.ticker,
            form_type=filing.form,
            filing_date=str(filing.filing_date),
            accession_no=filing.accession_no,
            section=section,
            page=page
        )
    ```

11. **Integrate citations into table parser** (1 hour)

    Update `src/parsers/table_parser.py`:
    ```python
    from ..utils.citations import Citation, create_citation_from_filing

    class TableParser:
        def parse_from_filing(...) -> ParsedTable:
            # ... existing parsing logic ...

            # Create citation
            citation = Citation(
                ticker=ticker,
                form_type=form_type,
                filing_date=filing.filing_date,
                accession_no=filing.accession_no,
                section="Item 8",  # Detect from context
                page=None  # Can extract from HTML if needed
            )

            return ParsedTable(
                markdown=markdown_table,
                structured=structured_data,
                citation=citation.to_string(),
                confidence="high",
                source_method="inline-xbrl"
            )
    ```

12. **Test citation generation** (30 min)
    ```bash
    # Unit test
    uv run pytest tests/test_citations.py -v

    # Integration test via API
    curl -X POST http://localhost:8000/api/v1/tables/parse \
      -d '{"ticker": "AAPL", ...}' | jq '.citation'

    # Expected: "[AAPL 10-K 2024, Item 8]"
    ```

**Checkpoint 3:** ✅ Every API response includes properly formatted citation

---

#### Afternoon Session (3-4 hours): Filings Endpoint

**Tasks:**

13. **Create filings endpoint** (2 hours)

    **File:** `src/api/routes/filings.py`
    ```python
    from fastapi import APIRouter, HTTPException, Query
    from typing import Optional
    import edgar
    from ...data.edgar_client import EdgarClient
    from ..models.responses import FilingResponse

    router = APIRouter()
    client = EdgarClient()

    @router.get("/{ticker}/{form_type}")
    async def get_filing(
        ticker: str,
        form_type: str,
        year: Optional[int] = Query(None, description="Filing year (default: latest)")
    ):
        """
        Retrieve metadata for a specific SEC filing.

        Returns filing information with citation and download URL.
        """
        try:
            company = edgar.Company(ticker)
            filings = company.get_filings(form=form_type)

            if year:
                filings = [f for f in filings if f.filing_date.year == year]

            if not filings:
                raise HTTPException(
                    status_code=404,
                    detail=f"No {form_type} filings found for {ticker}"
                )

            filing = filings[0]  # Latest

            return {
                "ticker": ticker,
                "form_type": form_type,
                "filing_date": str(filing.filing_date),
                "accession_no": filing.accession_no,
                "url": filing.url,
                "citation": f"[{ticker} {form_type} {filing.filing_date.year}]",
                "sections_available": [
                    "Item 1", "Item 1A", "Item 7", "Item 8"
                ]  # Can extract dynamically
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/{ticker}/{form_type}/sections")
    async def list_sections(ticker: str, form_type: str, year: Optional[int] = None):
        """List available sections in a filing (for discovery)."""
        # TODO: Implement section extraction
        return {
            "ticker": ticker,
            "form_type": form_type,
            "sections": ["Item 1", "Item 1A", "Item 7", "Item 8", "Item 15"]
        }
    ```

14. **Test filings endpoint** (1 hour)
    ```bash
    # Get latest 10-K metadata
    curl http://localhost:8000/api/v1/filings/AAPL/10-K | jq

    # Get specific year
    curl "http://localhost:8000/api/v1/filings/AAPL/10-K?year=2024" | jq

    # List sections
    curl http://localhost:8000/api/v1/filings/AAPL/10-K/sections | jq
    ```

**Checkpoint 4:** ✅ Can retrieve filing metadata via API

---

### **Day 3: Python SDK** (6-8 hours)

**Goal:** Ship installable Python SDK for easy integration

#### Full Day: SDK Implementation

**Tasks:**

15. **Create SDK package structure** (30 min)
    ```bash
    mkdir -p sdk/sec_api_llm/resources
    touch sdk/sec_api_llm/{__init__.py,client.py,exceptions.py,models.py}
    touch sdk/sec_api_llm/resources/{__init__.py,filings.py,tables.py}
    ```

16. **Create SDK client class** (2 hours)

    **File:** `sdk/sec_api_llm/client.py`
    ```python
    from typing import Optional
    import httpx

    from .resources.filings import FilingsResource
    from .resources.tables import TablesResource
    from .exceptions import SecApiError

    class SecClient:
        """
        Python client for SEC API for LLMs.

        Usage:
            client = SecClient(api_key="sk-...")
            table = client.tables.parse(ticker="AAPL", form="10-K", table="segment_info")
            print(table.markdown)
        """

        def __init__(
            self,
            api_key: Optional[str] = None,
            base_url: str = "http://localhost:8000",
            timeout: int = 30
        ):
            self.api_key = api_key
            self.base_url = base_url.rstrip("/")
            self.timeout = timeout

            # HTTP client
            self._client = httpx.Client(
                base_url=self.base_url,
                timeout=timeout,
                headers=self._get_headers()
            )

            # Resources
            self.filings = FilingsResource(self)
            self.tables = TablesResource(self)

        def _get_headers(self) -> dict:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            return headers

        def _request(self, method: str, path: str, **kwargs):
            """Make HTTP request with error handling."""
            try:
                response = self._client.request(method, path, **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                raise SecApiError(f"API error: {e.response.status_code} - {e.response.text}")
            except httpx.RequestError as e:
                raise SecApiError(f"Request failed: {str(e)}")

        def close(self):
            """Close HTTP client."""
            self._client.close()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.close()
    ```

17. **Create tables resource** (2 hours)

    **File:** `sdk/sec_api_llm/resources/tables.py`
    ```python
    from typing import TYPE_CHECKING
    from ..models import ParsedTable

    if TYPE_CHECKING:
        from ..client import SecClient

    class TablesResource:
        """Tables resource for parsing SEC tables."""

        def __init__(self, client: "SecClient"):
            self._client = client

        def parse(
            self,
            ticker: str,
            form: str,
            table: str,
            year: int = None
        ) -> ParsedTable:
            """
            Parse a table from SEC filing.

            Args:
                ticker: Stock ticker (e.g., "AAPL")
                form: Form type (e.g., "10-K")
                table: Table identifier (e.g., "segment_information")
                year: Filing year (default: latest)

            Returns:
                ParsedTable with markdown, structured data, and citation

            Example:
                table = client.tables.parse(
                    ticker="AAPL",
                    form="10-K",
                    table="segment_information",
                    year=2024
                )
                print(table.markdown)
                print(table.citation)
            """
            data = {
                "ticker": ticker,
                "form_type": form,
                "table_name": table,
                "year": year or 2024
            }

            response = self._client._request(
                "POST",
                "/api/v1/tables/parse",
                json=data
            )

            return ParsedTable(**response)
    ```

18. **Create response models** (1 hour)

    **File:** `sdk/sec_api_llm/models.py`
    ```python
    from dataclasses import dataclass
    from typing import List, Dict, Optional

    @dataclass
    class ParsedTable:
        """Parsed table with structured data."""
        markdown: str
        structured: List[Dict]
        citation: str
        confidence: str
        metadata: Dict

        def __str__(self) -> str:
            return self.markdown

        def __repr__(self) -> str:
            return f"ParsedTable(citation='{self.citation}', rows={len(self.structured)})"

    @dataclass
    class Filing:
        """SEC filing metadata."""
        ticker: str
        form_type: str
        filing_date: str
        accession_no: str
        url: str
        citation: str
        sections_available: List[str]
    ```

19. **Create SDK pyproject.toml** (30 min)

    **File:** `sdk/pyproject.toml`
    ```toml
    [project]
    name = "sec-api-llm"
    version = "0.1.0"
    description = "Python SDK for SEC API for LLMs"
    authors = [{name = "Wolfgang Schoenberger"}]
    requires-python = ">=3.10"
    dependencies = [
        "httpx>=0.27.0",
        "pydantic>=2.0.0",
    ]

    [project.urls]
    Homepage = "https://github.com/yourusername/sec-api-llm"
    Documentation = "https://docs.sec-api-llm.dev"

    [build-system]
    requires = ["hatchling"]
    build-backend = "hatchling.build"
    ```

20. **Create SDK README** (1 hour)

    **File:** `sdk/README.md`
    ```markdown
    # SEC API for LLMs - Python SDK

    Official Python SDK for the SEC API for LLMs.

    ## Installation

    ```bash
    pip install sec-api-llm
    ```

    ## Quick Start

    ```python
    from sec_api_llm import SecClient

    client = SecClient()

    # Parse a table from Apple's 10-K
    table = client.tables.parse(
        ticker="AAPL",
        form="10-K",
        table="segment_information",
        year=2024
    )

    print(table.markdown)
    # | Region | Revenue |
    # |--------|---------|
    # | Americas | $178B |
    # ...

    print(table.citation)
    # [AAPL 10-K 2024, Item 8]
    ```

    ## Features

    - ✅ **Structured table parsing** (100% accuracy)
    - ✅ **Citations** for every response
    - ✅ **Type hints** for better IDE support
    - ✅ **Error handling** with descriptive messages

    ## API Reference

    ### `client.tables.parse()`

    Parse a table from SEC filing.

    **Parameters:**
    - `ticker` (str): Stock ticker symbol
    - `form` (str): Form type (10-K, 10-Q, 8-K)
    - `table` (str): Table identifier
    - `year` (int, optional): Filing year

    **Returns:** `ParsedTable` with:
    - `markdown`: Markdown-formatted table
    - `structured`: List of dicts with table data
    - `citation`: Source citation string
    - `confidence`: Parsing confidence (high/medium/low)
    ```

21. **Test SDK locally** (1 hour)
    ```bash
    # Install SDK in editable mode
    cd sdk
    pip install -e .

    # Test import
    python -c "from sec_api_llm import SecClient; print('✅ SDK imported')"

    # Test full flow
    python <<EOF
    from sec_api_llm import SecClient

    client = SecClient(base_url="http://localhost:8000")
    table = client.tables.parse(
        ticker="AAPL",
        form="10-K",
        table="segment_information",
        year=2024
    )

    print("Markdown:")
    print(table.markdown)
    print("\nCitation:", table.citation)
    print("✅ SDK works!")
    EOF
    ```

**Checkpoint 5:** ✅ SDK installable and functional

---

## Testing Strategy

### Unit Tests (Write as you go)

```bash
# Directory: tests/api/

# Test files to create:
tests/api/
├── test_health.py          # Test health endpoint
├── test_tables.py          # Test table parsing endpoint
├── test_filings.py         # Test filing metadata endpoint
└── test_citations.py       # Test citation formatting
```

**Example test:**
```python
# tests/api/test_tables.py
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_parse_table_success():
    """Test successful table parsing."""
    response = client.post(
        "/api/v1/tables/parse",
        json={
            "ticker": "AAPL",
            "form_type": "10-K",
            "year": 2024,
            "table_name": "segment_information"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "markdown" in data
    assert "citation" in data
    assert "AAPL 10-K 2024" in data["citation"]

def test_parse_table_invalid_ticker():
    """Test error handling for invalid ticker."""
    response = client.post(
        "/api/v1/tables/parse",
        json={
            "ticker": "INVALID",
            "form_type": "10-K",
            "year": 2024,
            "table_name": "segment_information"
        }
    )

    assert response.status_code in [404, 500]
```

### Integration Tests (Day 3 end)

**Create demo script:**
```python
# scripts/demo_api.py
"""
Demo script for user interviews.
Shows all Tier 0 capabilities.
"""
from sec_api_llm import SecClient

def main():
    print("🚀 SEC API for LLMs - Demo\n")

    client = SecClient(base_url="http://localhost:8000")

    # Demo 1: Table parsing
    print("1️⃣ Parsing Apple segment table...")
    table = client.tables.parse(
        ticker="AAPL",
        form="10-K",
        table="segment_information",
        year=2024
    )
    print(f"   Citation: {table.citation}")
    print(f"   Rows: {len(table.structured)}")
    print(f"\n{table.markdown}\n")

    # Demo 2: Filing metadata
    print("2️⃣ Fetching filing metadata...")
    filing = client.filings.get(ticker="AAPL", form="10-K")
    print(f"   Filing date: {filing.filing_date}")
    print(f"   URL: {filing.url}")
    print(f"   Citation: {filing.citation}\n")

    print("✅ All demos complete!")

if __name__ == "__main__":
    main()
```

**Run demo:**
```bash
uv run python scripts/demo_api.py
```

---

## Dependencies and Prerequisites

### Required Packages (Add to pyproject.toml)

```toml
[project.dependencies]
# Existing
edgartools = ">=3.0.0"
openai = ">=1.0.0"
anthropic = ">=0.18.0"
chromadb = ">=0.4.0"
beautifulsoup4 = ">=4.12.0"
lxml = ">=5.0.0"
pandas = ">=2.2.0"
tabulate = ">=0.9.0"

# NEW - Tier 0
fastapi = ">=0.109.0"
uvicorn = {version = ">=0.27.0", extras = ["standard"]}
pydantic = ">=2.5.0"
pydantic-settings = ">=2.1.0"
httpx = ">=0.27.0"
```

### Environment Setup

```bash
# .env file additions
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true  # Development only
API_WORKERS=1    # Single worker for demo
```

---

## Potential Challenges and Edge Cases

### Challenge 1: Table Identification
**Problem:** User provides table name that doesn't match filing
**Solution:**
- Fuzzy matching on table names
- Return list of available tables if exact match fails
- Clear error message: "Table 'xyz' not found. Available: [...]"

### Challenge 2: Rate Limiting (SEC)
**Problem:** Hitting SEC's 10 req/sec limit during demo
**Solution:**
- Implement simple file cache (cache parsed tables for 30 days)
- Add retry logic with exponential backoff
- Cache filing metadata separately

### Challenge 3: Parsing Failures
**Problem:** Some tables might not have inline XBRL tags
**Solution:**
- Return `confidence: "low"` for unparsed tables
- Fallback: Return raw HTML with `##TABLE_START` markers
- Clear error message explaining limitation

### Challenge 4: SDK Version Sync
**Problem:** API and SDK versions might get out of sync during development
**Solution:**
- Keep SDK in same repo (monorepo)
- Version API responses with `/api/v1/` prefix
- SDK includes API version in requests

---

## Success Criteria (Detailed)

| Component | Must Have | Nice to Have | Validation |
|-----------|-----------|--------------|------------|
| **FastAPI Backend** | ✅ Runs on localhost<br>✅ Swagger docs accessible<br>✅ Health endpoint | ⚪ Deployed to fly.io<br>⚪ Custom domain | `curl /health` returns 200 |
| **Table Parsing** | ✅ Parses AAPL segment table<br>✅ Returns Markdown<br>✅ 100% accuracy | ⚪ Multiple table types<br>⚪ Auto-detection | Compare with ground truth CSV |
| **Citations** | ✅ Every response has citation<br>✅ Format: `[TICKER FORM YEAR, Sec]` | ⚪ Page numbers<br>⚪ Clickable URLs | Manual inspection of responses |
| **Python SDK** | ✅ pip installable<br>✅ `client.tables.parse()` works<br>✅ Type hints | ⚪ Async support<br>⚪ Published to PyPI | `pip install -e sdk/` succeeds |
| **Demo** | ✅ Can run full demo in <2 min<br>✅ Works on localhost | ⚪ Public URL for remote interviews | Run `scripts/demo_api.py` |

---

## Deployment (Optional - If Time Permits)

### Quick Deploy to fly.io (1 hour)

**Only if you want to demo over the internet (not localhost).**

```bash
# Install flyctl
brew install flyctl

# Login
fly auth login

# Initialize app
fly launch --name sec-api-llm

# Deploy
fly deploy

# Get URL
fly status
```

**Benefits:**
- Remote user interviews (no localhost tunneling)
- Persistent URL for landing page screenshots
- Test deployment process

**Drawback:**
- Takes time away from core development
- Not necessary for validation

**Recommendation:** Skip deployment for Tier 0, use localhost + ngrok for remote demos.

---

## Files to Create (Checklist)

### API (Day 1-2)
- [ ] `src/api/__init__.py`
- [ ] `src/api/main.py`
- [ ] `src/api/dependencies.py`
- [ ] `src/api/routes/__init__.py`
- [ ] `src/api/routes/health.py`
- [ ] `src/api/routes/filings.py`
- [ ] `src/api/routes/tables.py`
- [ ] `src/api/models/__init__.py`
- [ ] `src/api/models/requests.py`
- [ ] `src/api/models/responses.py`

### Parsers (Day 1)
- [ ] `src/parsers/__init__.py`
- [ ] `src/parsers/table_parser.py`
- [ ] `src/parsers/inline_xbrl.py` (optional split)

### Utils (Day 2)
- [ ] `src/utils/citations.py`
- [ ] `src/utils/formatting.py`

### SDK (Day 3)
- [ ] `sdk/sec_api_llm/__init__.py`
- [ ] `sdk/sec_api_llm/client.py`
- [ ] `sdk/sec_api_llm/exceptions.py`
- [ ] `sdk/sec_api_llm/models.py`
- [ ] `sdk/sec_api_llm/resources/__init__.py`
- [ ] `sdk/sec_api_llm/resources/filings.py`
- [ ] `sdk/sec_api_llm/resources/tables.py`
- [ ] `sdk/pyproject.toml`
- [ ] `sdk/README.md`

### Tests (Day 1-3)
- [ ] `tests/api/test_health.py`
- [ ] `tests/api/test_tables.py`
- [ ] `tests/api/test_filings.py`
- [ ] `tests/api/test_citations.py`

### Scripts (Day 3)
- [ ] `scripts/demo_api.py`
- [ ] `scripts/run_dev.sh` (optional)

---

## Next Steps After Tier 0

Once Tier 0 is complete, you can:

1. **User Interviews (Immediate):**
   - Demo working API to 5-10 potential users
   - Validate pricing ($49-$249/mo)
   - Get feedback on features that matter
   - Record: "Would you pay for this?"

2. **Landing Page (Week 4):**
   - Build simple page with demo video
   - Show API examples with real responses
   - Collect 100 waitlist signups

3. **Tier 1 Development (After validation):**
   - Semantic search with embeddings
   - Temporal change detection
   - More table types

---

## Changelog

| Date | Author | Changes |
|------|--------|---------|
| 12/11/2025 04:53 AM PST (via pst-timestamp) | Claude/Wolfgang | Initial Tier 0 implementation plan created |

---

**Status:** ✅ **READY TO IMPLEMENT**

This plan provides 2-3 days of focused work to build a demo-able MVP that proves all three core differentiators. Let's ship it! 🚀
