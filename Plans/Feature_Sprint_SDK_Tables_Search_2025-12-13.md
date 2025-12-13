# Feature Sprint: SDK + Table Expansion + Semantic Search

**Created:** 12/13/2025 01:10 AM PST (via pst-timestamp)
**Completed:** 12/13/2025 01:19 AM PST (via pst-timestamp)
**Goal:** Expand feature set before user interviews
**Status:** COMPLETED

---

## Overview

Three features to implement in sequence:
1. **Python SDK** - Developer-friendly client library
2. **Table Type Expansion** - Support more financial table types
3. **Semantic Search API** - Vector search endpoint

---

## Option A: Python SDK

**Estimated Time:** 4-6 hours
**Priority:** T0 - High Impact

### Deliverables
- [x] `sdk/sec_api_llm/` package structure
- [x] `SecClient` class with resource-based API
- [x] `client.tables.parse()` - Table parsing
- [x] `client.filings.get()` - Filing metadata
- [x] `client.filings.list()` - List filings
- [x] `sdk/pyproject.toml` - Package config
- [x] Basic error handling and exceptions
- [x] Installable via `pip install -e sdk/`
- [x] `client.search.semantic()` - Semantic search (bonus)

### API Design
```python
from sec_api_llm import SecClient

client = SecClient(base_url="http://localhost:8000")

# Tables
table = client.tables.parse(ticker="AAPL", form="10-K", year=2024)
print(table.markdown)
print(table.citation)

# Filings
filing = client.filings.get(ticker="AAPL", form="10-K", year=2024)
filings = client.filings.list(ticker="AAPL", form="10-K", limit=5)
```

---

## Option B: Table Type Expansion

**Estimated Time:** 4-6 hours
**Priority:** T0 - High Impact

### Deliverables
- [x] Income statement parsing via XBRL (already implemented)
- [x] Balance sheet parsing via XBRL (already implemented)
- [x] Cash flow statement parsing via XBRL (already implemented)
- [x] API endpoint updates to support table types
- [x] SDK updates for new table types

### Supported Tables (After)
| Table Type | Source | Status |
|------------|--------|--------|
| Segment Information | Inline XBRL | ✅ Existing |
| Income Statement | XBRL Financials | New |
| Balance Sheet | XBRL Financials | New |
| Cash Flow Statement | XBRL Financials | New |

### API Design
```python
# Via SDK
income = client.tables.parse(ticker="AAPL", table_type="income_statement", year=2024)
balance = client.tables.parse(ticker="AAPL", table_type="balance_sheet", year=2024)
cashflow = client.tables.parse(ticker="AAPL", table_type="cash_flow", year=2024)

# Via API
POST /api/v1/tables/parse
{
  "ticker": "AAPL",
  "table_type": "income_statement",  # NEW field
  "year": 2024
}
```

---

## Option C: Semantic Search API

**Estimated Time:** 4-6 hours
**Priority:** T1 - Medium Impact

### Deliverables
- [x] `/api/v1/search/` endpoint (semantic search)
- [x] Integration with existing ChromaDB vector store
- [x] Filing section indexing on-demand
- [x] SDK `client.search.semantic()` method
- [x] Citation in search results (improved formatting)

### API Design
```python
# Via SDK
results = client.search.semantic(
    query="risk factors mentioning China supply chain",
    ticker="AAPL",  # Optional filter
    form="10-K",    # Optional filter
    limit=10
)

for result in results:
    print(result.text)
    print(result.citation)
    print(result.score)

# Via API
POST /api/v1/search/semantic
{
  "query": "risk factors mentioning China supply chain",
  "ticker": "AAPL",
  "form": "10-K",
  "limit": 10
}
```

### Implementation Notes
- Use existing `src/data/vector_store.py`
- Index filing sections on first search (lazy indexing)
- Cache embeddings for common filings
- Return top-k results with citations

---

## Execution Order

```
┌─────────────────────────────────────────────────────────────┐
│  Option A: SDK        Option B: Tables      Option C: Search │
│  ─────────────        ────────────────      ──────────────── │
│  1. Package setup     1. XBRL integration   1. API endpoint  │
│  2. SecClient         2. Income stmt        2. Vector store  │
│  3. TablesResource    3. Balance sheet      3. Indexing      │
│  4. FilingsResource   4. Cash flow          4. SDK method    │
│  5. Test & verify     5. API updates        5. Test & verify │
│                       6. SDK updates                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Success Criteria

| Feature | Criterion | Status |
|---------|-----------|--------|
| SDK | `pip install -e sdk/` works | ✅ |
| SDK | `client.tables.parse()` returns data | ✅ |
| SDK | `client.filings.get()` returns metadata | ✅ |
| SDK | `client.search.semantic()` works | ✅ |
| Tables | Income statement parses correctly | ✅ |
| Tables | Balance sheet parses correctly | ✅ |
| Tables | Cash flow parses correctly | ✅ |
| Tables | Segment information parses correctly | ✅ |
| Search | Semantic search returns relevant results | ✅ |
| Search | Results include citations | ✅ |

**All criteria met!**

---

## Changelog

| Timestamp | Change |
|-----------|--------|
| 12/13/2025 01:10 AM PST (via pst-timestamp) | Initial plan created |
| 12/13/2025 01:12 AM PST | Option A: Fixed SDK URL paths, added SearchResource |
| 12/13/2025 01:15 AM PST | Option A: Verified SDK installation and all resources working |
| 12/13/2025 01:16 AM PST | Option B: Verified all table types already implemented |
| 12/13/2025 01:18 AM PST | Option C: Improved search citation formatting |
| 12/13/2025 01:19 AM PST (via pst-timestamp) | All options complete, plan marked DONE |

