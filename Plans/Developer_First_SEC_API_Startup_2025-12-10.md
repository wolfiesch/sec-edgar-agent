# Developer-First SEC API Startup: Master Design Document

**Created:** 12/10/2025 05:23 PM PST (via pst-timestamp)
**Last Updated:** 12/10/2025 05:34 PM PST (via pst-timestamp)
**Status:** Draft - Strategic Planning Phase
**Document Type:** Master Design Document

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Vision & Mission](#vision--mission)
3. [Killer Features](#killer-features) ← NEW
4. [Market Opportunity](#market-opportunity)
5. [Product Strategy](#product-strategy)
6. [Technical Architecture](#technical-architecture)
7. [Critical Technical Challenges](#critical-technical-challenges) ← NEW
8. [Go-to-Market Strategy](#go-to-market-strategy)
9. [Implementation Roadmap](#implementation-roadmap)
10. [Business Model](#business-model)
11. [Competitive Analysis](#competitive-analysis)
12. [Risk Assessment](#risk-assessment)
13. [Success Metrics](#success-metrics)
14. [Open Questions](#open-questions)
15. [Immediate Next Steps](#immediate-next-steps) ← NEW
16. [Changelog](#changelog)

---

## Executive Summary

### The Opportunity

Build the **"Stripe of financial research APIs"** - an LLM-native data infrastructure that provides semantically chunked, pre-tagged SEC filing data through a simple, developer-first experience.

### Why Now

- LLM in finance market: $7.79B (2025) → $130.65B (2034) at 36.8% CAGR
- 61% of CFOs haven't implemented AI yet (early adopter window)
- No existing solution is purpose-built for AI/LLM consumption
- Existing tools (Bloomberg $24k/yr, AlphaSense $10-20k/seat) price out smaller players

### The Differentiator

**Current solutions are data-first:**
```
Developer Query → REST API → Raw JSON/CSV → Developer parses → Feeds to LLM
```

**Our solution is LLM-native:**
```
Developer Query → API → Pre-chunked, embedded, citation-tagged data → Ready for RAG
```

### Target Outcome

- **Year 1:** 1,000 free users, 100 paid customers, $120k ARR
- **Year 2:** 10 enterprise customers, expand to disclosure formatting tool, $500k ARR
- **Year 3:** Series A or profitable bootstrap at $2M+ ARR

---

## Vision & Mission

### Vision

**"Every financial AI application is powered by our infrastructure."**

### Mission

Democratize access to intelligent financial data by building the most developer-friendly, LLM-optimized SEC data infrastructure.

### Core Beliefs

1. **Citation is non-negotiable** - Financial AI without verifiable sources is liability
2. **Developer experience is product** - If it takes >5 minutes to integrate, we've failed
3. **LLM-native is the future** - Pre-processing for AI consumption is table stakes
4. **Transparency builds trust** - Simple pricing, open documentation, no sales required

---

## Killer Features

> *"These are our moats. If we execute on these three things exceptionally well, we win."*

### 1. Citation-Native Architecture (The Trust Moat)

**Why This Matters:**
- General-purpose RAG tools (LangChain default splitters) are terrible at financial documents
- They split text mid-sentence, lose header context, orphan table data
- Compliance officers at banks will **never** approve an LLM app that can't trace a number back to source

**Our Guarantee:**
Every single chunk returns: `[TICKER, FORM, ITEM, PAGE, URL]`

```python
# Every response is audit-ready
{
    "text": "Revenue decreased 15% due to supply chain disruptions...",
    "citation": {
        "ticker": "AAPL",
        "form": "10-K",
        "item": "Item 7 - MD&A",
        "page": 34,
        "url": "https://sec.gov/Archives/edgar/data/320193/..."
    }
}
```

**Marketing Angle:** "The only API where compliance can verify every AI output."

### 2. Temporal Change Detection (The "Diff" Killer Feature)

**Why This Matters:**
- Analysts spend **hours** manually comparing this year's Risk Factors to last year's
- Nobody else offers this as a first-class feature
- This is what makes us indispensable, not just useful

**The Data Model:**
```python
class FilingChunk:
    # ... other fields ...

    # KILLER FEATURE - Temporal tracking
    first_appeared: str        # "2019-10K" - When did this language first appear?
    changed_from_prior: bool   # True if modified from last filing
    change_type: str           # "new" | "modified" | "removed" | "unchanged"
    prior_text: str            # The previous version (for diffs)
```

**API Example:**
```python
# One API call replaces hours of manual work
changes = client.detect_changes(
    company="NVDA",
    section="risk_factors",
    compare=["2023-10K", "2024-10K"]
)

# Returns:
# - New risks added (e.g., "AI chip export restrictions")
# - Risks removed
# - Language that intensified ("significant" → "material")
```

**Marketing Angle:** "See exactly what changed. Every year. Every company. In seconds."

### 3. Pre-Computed Embeddings (The Cost/Speed Moat)

**Developer Cost Savings:**
- OpenAI embeddings: ~$0.10 per 1M tokens
- Processing 10,000 10-Ks = ~$500-1,000 in embedding costs alone
- Plus days of engineering time to build the pipeline

**Our Value:**
```python
# Embeddings included - no extra API calls needed
chunk = client.get_chunk("nvda-10k-2024-risk-007")

print(chunk.text)       # The content
print(chunk.embedding)  # Ready for your vector DB - no OpenAI call needed
print(chunk.citation)   # Full provenance
```

**Marketing Angle:** "RAG-ready in 5 minutes. Not 5 days."

---

## Market Opportunity

### Total Addressable Market (TAM): ~$1B

| Segment | TAM | Description |
|---------|-----|-------------|
| Fintech Builders | $500M | 10,000+ companies building financial analysis tools, robo-advisors |
| Emerging Asset Managers | $200M | 5,000+ funds with $10M-$500M AUM |
| Financial AI Startups | $300M | Companies building AI financial assistants, research tools |

### Serviceable Addressable Market (SAM): ~$200M

- Developers/companies actively building LLM-powered financial tools
- Price point: $99-$10,000/year

### Serviceable Obtainable Market (SOM): $2-5M (Year 3)

- 500 paid customers × $4,000 average annual contract value

### Market Dynamics

| Factor | Status | Implication |
|--------|--------|-------------|
| LLM Adoption | Accelerating (36.8% CAGR) | Timing is right |
| Trust Barrier | High (zero tolerance for errors) | Citation-first wins |
| Enterprise Adoption | Early (61% haven't implemented) | Land-and-expand opportunity |
| Pricing Gap | Significant (Bloomberg $24k vs our $99) | Long tail underserved |

---

## Product Strategy

### Core Product: Edgar API

**One-liner:** "LLM-ready SEC data with citations in every response."

### Key Features (Priority Order)

#### T0 - Must Have (MVP)

| Feature | Description | Value Proposition |
|---------|-------------|-------------------|
| **Semantic Search** | Natural language queries across SEC filings | "Find risk factors mentioning China" in one API call |
| **Citation-Native** | Every chunk includes `[TICKER FORM YEAR, Section, Page]` | Verifiable AI outputs, audit-ready |
| **Pre-Chunked Data** | Optimized for LLM context windows | No token waste, better retrieval |
| **Pre-Computed Embeddings** | Vector representations included | Save $0.10/1M tokens + dev time |

#### T1 - Should Have (Post-MVP)

| Feature | Description | Value Proposition |
|---------|-------------|-------------------|
| **Temporal Analysis** | Year-over-year change detection | "How did NVDA's China risk evolve?" |
| **XBRL Tag Extraction** | Raw XBRL tags mapped to text (NOT full normalization) | Developers decide how to calculate metrics |
| **Relationship Graphs** | Pre-computed peer groups, suppliers | Competitive analysis ready |
| **SDKs** | Python, JavaScript, TypeScript | 5-minute integration |

> **Note on Standardized Financials:** Full normalization of metrics like "Adjusted EBITDA" across 5,000 companies is a startup in itself. Instead, we provide **raw XBRL tags mapped to their source text**, letting developers make their own standardization decisions. This is faster to build and more flexible for users.

#### T2 - Nice to Have (Scale)

| Feature | Description | Value Proposition |
|---------|-------------|-------------------|
| **Streaming** | Real-time new filing alerts | Watchlist-style monitoring |
| **Custom Tagging** | User-defined semantic tags | Domain-specific applications |
| **Enterprise SSO** | SAML/OIDC integration | Security compliance |
| **Audit Logs** | Full API access history | Regulatory requirements |

### Product Principles

1. **5 Lines of Code** - Any core use case achievable in minimal code
2. **Fail Gracefully** - Clear error messages, helpful debugging
3. **Progressively Complex** - Simple defaults, power user options
4. **Documentation-First** - Docs are product, not afterthought

### API Design Preview

```python
# Installation
pip install edgar-api

# Basic Usage
from edgar_api import EdgarClient

client = EdgarClient(api_key="sk_test_...")

# Semantic search with citations
results = client.search(
    query="supply chain disruption risks",
    companies=["AAPL", "TSMC", "NVDA"],
    forms=["10-K", "10-Q"],
    years=[2023, 2024]
)

for chunk in results.chunks:
    print(f"{chunk.text}")
    print(f"Citation: {chunk.citation}")  # [AAPL 10-K 2024, Item 1A, p.12]
    print(f"Embedding: {chunk.embedding[:5]}...")  # Pre-computed vector

# Financial data with normalization
financials = client.get_financials(
    company="AAPL",
    metrics=["revenue", "gross_margin", "r_and_d"],
    periods=["FY2022", "FY2023", "FY2024"]
)

# Temporal analysis
changes = client.detect_changes(
    company="NVDA",
    section="risk_factors",
    compare=["2023-10K", "2024-10K"]
)
```

---

## Technical Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                 │
├─────────────────────────────────────────────────────────────────────┤
│  Python SDK  │  JavaScript SDK  │  REST API  │  GraphQL (future)   │
└──────────────┴──────────────────┴────────────┴─────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY                                  │
├─────────────────────────────────────────────────────────────────────┤
│  Authentication  │  Rate Limiting  │  Usage Tracking  │  Caching   │
└──────────────────┴─────────────────┴──────────────────┴────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       SERVICE LAYER                                  │
├─────────────────────────────────────────────────────────────────────┤
│  Search Service  │  Filing Service  │  Analytics Service  │  ...   │
└──────────────────┴──────────────────┴─────────────────────┴────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                   │
├────────────────┬────────────────┬────────────────┬──────────────────┤
│  Vector Store  │   PostgreSQL   │  Redis Cache   │  Object Storage  │
│  (Embeddings)  │   (Metadata)   │  (Hot Data)    │  (Raw Filings)   │
└────────────────┴────────────────┴────────────────┴──────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      INGESTION PIPELINE                              │
├─────────────────────────────────────────────────────────────────────┤
│  SEC Scraper  →  Parser  →  Chunker  →  Embedder  →  Tagger  →  DB │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Details

#### 1. Ingestion Pipeline

**Purpose:** Transform raw SEC filings into LLM-ready chunks

```
Raw Filing (HTML/XBRL)
    │
    ▼
┌─────────────────┐
│  SEC Scraper    │  ← Rate-limited to 10 req/sec (SEC requirement)
│  - Full-text    │
│  - XBRL data    │
│  - Metadata     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Parser         │  ← Extract sections, tables, financials
│  - Section ID   │
│  - Table parse  │
│  - XBRL decode  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Chunker        │  ← Semantic chunking (not arbitrary splits)
│  - Context-aware│
│  - Citation gen │
│  - ~500 tokens  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Embedder       │  ← Generate vector representations
│  - OpenAI/local │
│  - 1536-dim     │
│  - Batch process│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Tagger         │  ← Apply semantic labels
│  - ASC topics   │
│  - Risk types   │
│  - Entities     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Storage        │  ← Persist to databases
│  - Vectors      │
│  - Metadata     │
│  - Raw backup   │
└─────────────────┘
```

#### 2. Data Models

**Filing Chunk (Core Entity)**

```python
class FilingChunk:
    # Identity
    chunk_id: str           # "aapl-10k-2024-risk-003"
    filing_id: str          # "aapl-10k-2024"

    # Content
    text: str               # The actual text content
    embedding: List[float]  # 1536-dim vector

    # Citation
    citation: Citation
    #   ticker: "AAPL"
    #   form: "10-K"
    #   period: "FY2024"
    #   section: "Item 1A - Risk Factors"
    #   page: 12
    #   url: "https://sec.gov/..."

    # Semantic Tags
    tags: Tags
    #   topics: ["china", "supply_chain", "geopolitical"]
    #   asc_topics: ["ASC 820", "ASC 606"]
    #   sentiment: "negative"
    #   materiality: "high"
    #   entities: ["Foxconn", "Taiwan"]

    # Temporal
    first_appeared: str     # "2019-10K"
    changed_from_prior: bool
    change_type: str        # "new" | "modified" | "removed"
```

**Standardized Financial**

```python
class StandardizedFinancial:
    # Identity
    company: str            # "AAPL"
    concept: str            # "total_revenue" (normalized)
    period: str             # "FY2024"

    # Value
    value: float            # 383285000000
    unit: str               # "USD"

    # Source
    source_xbrl_tag: str    # "RevenueFromContractWithCustomer..."
    citation: Citation

    # Comparability
    comparable_to: List[str]  # ["MSFT.total_revenue", "GOOGL.total_revenue"]
    confidence: float         # 0.99
```

#### 3. Database Schema

**PostgreSQL (Metadata & Relationships)**

```sql
-- Companies
CREATE TABLE companies (
    cik VARCHAR(10) PRIMARY KEY,
    ticker VARCHAR(10),
    name VARCHAR(255),
    sector VARCHAR(100),
    industry VARCHAR(100),
    sic_code VARCHAR(10),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Filings
CREATE TABLE filings (
    filing_id VARCHAR(50) PRIMARY KEY,
    cik VARCHAR(10) REFERENCES companies(cik),
    form_type VARCHAR(20),
    filed_date DATE,
    period_end DATE,
    accession_number VARCHAR(25),
    url TEXT,
    processed_at TIMESTAMP,
    chunk_count INTEGER
);

-- Chunks (metadata only, text/embeddings in vector store)
CREATE TABLE chunks (
    chunk_id VARCHAR(100) PRIMARY KEY,
    filing_id VARCHAR(50) REFERENCES filings(filing_id),
    section VARCHAR(100),
    page_start INTEGER,
    page_end INTEGER,
    token_count INTEGER,
    tags JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Standardized Financials
CREATE TABLE financials (
    id SERIAL PRIMARY KEY,
    filing_id VARCHAR(50) REFERENCES filings(filing_id),
    concept VARCHAR(100),
    value NUMERIC,
    unit VARCHAR(10),
    source_xbrl_tag VARCHAR(255),
    confidence FLOAT
);

-- Indexes
CREATE INDEX idx_filings_ticker_date ON filings(cik, filed_date DESC);
CREATE INDEX idx_chunks_filing ON chunks(filing_id);
CREATE INDEX idx_chunks_tags ON chunks USING GIN(tags);
CREATE INDEX idx_financials_concept ON financials(concept, filing_id);
```

**Vector Store (ChromaDB → Pinecone at scale)**

```python
# Collection structure
collection = {
    "name": "sec_filings",
    "metadata": {
        "hnsw:space": "cosine"
    }
}

# Document structure
{
    "id": "aapl-10k-2024-risk-003",
    "embedding": [0.1, 0.2, ...],  # 1536 dimensions
    "metadata": {
        "ticker": "AAPL",
        "form": "10-K",
        "period": "FY2024",
        "section": "risk_factors",
        "page": 12,
        "topics": ["china", "supply_chain"],
        "filed_date": "2024-10-31"
    },
    "document": "We face significant risks related to our supply chain..."
}
```

#### 4. API Endpoints

**Core Endpoints (MVP)**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/search` | POST | Semantic search across filings |
| `/v1/filings/{filing_id}` | GET | Get filing metadata and chunks |
| `/v1/companies/{ticker}` | GET | Company info and filing list |
| `/v1/financials/{ticker}` | GET | Standardized financial data |
| `/v1/chunks/{chunk_id}` | GET | Single chunk with full detail |

**Extended Endpoints (Post-MVP)**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/compare` | POST | Compare sections across filings |
| `/v1/changes` | POST | Detect temporal changes |
| `/v1/peers/{ticker}` | GET | Peer group and comparisons |
| `/v1/stream` | WS | Real-time new filing alerts |

**Example Request/Response**

```bash
# Request
POST /v1/search
{
    "query": "supply chain risks related to China",
    "filters": {
        "tickers": ["AAPL", "NVDA", "TSMC"],
        "forms": ["10-K"],
        "years": [2023, 2024]
    },
    "options": {
        "include_embeddings": true,
        "limit": 10
    }
}

# Response
{
    "results": [
        {
            "chunk_id": "nvda-10k-2024-risk-007",
            "text": "Our operations in China and Taiwan expose us to significant geopolitical risks...",
            "embedding": [0.12, -0.34, ...],
            "citation": {
                "ticker": "NVDA",
                "form": "10-K",
                "period": "FY2024",
                "section": "Item 1A - Risk Factors",
                "page": 23,
                "url": "https://www.sec.gov/Archives/edgar/data/..."
            },
            "tags": {
                "topics": ["china", "taiwan", "geopolitical", "supply_chain"],
                "sentiment": "negative",
                "materiality": "high"
            },
            "score": 0.92
        },
        // ... more results
    ],
    "metadata": {
        "total_results": 47,
        "query_time_ms": 142,
        "credits_used": 1
    }
}
```

#### 5. Infrastructure

**MVP Infrastructure (~$550-1,000/month)**

| Component | Service | Cost/Month | Notes |
|-----------|---------|------------|-------|
| API Server | Railway/Render | $50-100 | Auto-scaling |
| PostgreSQL | Railway/Supabase | $25-50 | Managed |
| Vector DB | ChromaDB on EC2 | $150 | Self-hosted |
| Redis | Upstash | $10-30 | Caching |
| Object Storage | S3 | $20-50 | Raw filings |
| Embeddings | OpenAI API | $100-300 | One-time corpus + incremental |
| Monitoring | Datadog/Sentry | $0-50 | Free tier initially |
| **Total** | | **$355-780** | |

**Scale Infrastructure ($2,000-5,000/month)**

| Component | Service | Cost/Month | Notes |
|-----------|---------|------------|-------|
| API Server | AWS ECS/EKS | $300-500 | Multi-region |
| PostgreSQL | AWS RDS | $200-400 | Multi-AZ |
| Vector DB | Pinecone | $500-1,000 | Managed, scalable |
| Redis | AWS ElastiCache | $100-200 | Clustered |
| Object Storage | S3 | $100-200 | Increased volume |
| CDN | CloudFront | $50-100 | API caching |
| Monitoring | Datadog | $100-200 | Full observability |
| **Total** | | **$1,350-2,600** | |

---

## Critical Technical Challenges

> *These are the hard problems. If we don't solve these, we don't have a product.*

### Challenge 1: The HTML Table Nightmare 🔴 CRITICAL

**The Problem:**
10-Ks are full of complex, multi-header tables (debt maturity schedules, segment information, lease commitments). If you feed a flattened table to an LLM without preserving row/column structure, **the LLM becomes a random number generator.**

**Why Standard Tools Fail:**
- `BeautifulSoup` + `pandas.read_html()` struggle with nested HTML tables in EDGAR filings
- Tables have merged cells, multi-level headers, footnotes
- Row context gets lost when flattened to text

**Example Problem Table (Apple Segment Information):**
```
┌──────────────────┬─────────┬─────────┬─────────┐
│                  │  2024   │  2023   │  2022   │
├──────────────────┼─────────┼─────────┼─────────┤
│ Americas         │         │         │         │
│   Net sales      │ $167.0B │ $162.6B │ $169.7B │
│   Operating inc. │  $62.7B │  $60.5B │  $62.7B │
├──────────────────┼─────────┼─────────┼─────────┤
│ Europe           │         │         │         │
│   Net sales      │  $94.3B │  $94.3B │ $102.0B │
│   ...            │         │         │         │
└──────────────────┴─────────┴─────────┴─────────┘
```

**Our Solution Strategy (Hybrid Approach):**

1. **Primary: [sec-parser](https://github.com/alphanome-ai/sec-parser)** (Open Source)
   - Purpose-built for SEC EDGAR HTML documents
   - Organizes filings into semantic elements and tree structure
   - Supports MemWalker for AI-assisted extraction

2. **Secondary: XBRL-First for Financial Tables**
   - Use [EdgarTools](https://edgartools.readthedocs.io/) for XBRL extraction
   - Financial statements are already structured in XBRL
   - Bypass HTML parsing entirely for numeric data

3. **Fallback: Layout-Aware Models**
   - [LayoutLM](https://huggingface.co/docs/transformers/model_doc/layoutlm) for complex tables
   - Vision models for table structure understanding
   - More expensive, reserve for edge cases

4. **Output Format:**
   ```python
   # Tables converted to LLM-readable format
   {
       "table_id": "aapl-10k-2024-segment-info",
       "format": "markdown",  # or "json_rows"
       "content": """
       | Region | Metric | 2024 | 2023 | 2022 |
       |--------|--------|------|------|------|
       | Americas | Net sales | $167.0B | $162.6B | $169.7B |
       | Americas | Operating income | $62.7B | $60.5B | $62.7B |
       ...
       """,
       "citation": { ... }
   }
   ```

**Validation Test (MUST PASS BEFORE MVP):**
- [ ] Parse Apple's Segment Information table from latest 10-K
- [ ] Output should be 100% accurate when fed to Claude/GPT-4
- [ ] If this fails, we don't have a product

---

### Challenge 2: Embedding "Rot" & Model Lock-in 🟡 MEDIUM

**The Problem:**
We plan to pre-compute embeddings (likely OpenAI `text-embedding-3-small`). But:
- What if a customer wants Cohere embeddings?
- What if OpenAI releases a new model and old vectors become stale?
- Pre-computed vectors lock customers into our embedding choice

**Solution: Tiered Embedding Strategy**

**MVP (Acceptable Lock-in):**
- Ship with OpenAI `text-embedding-3-small` (1536 dimensions)
- This is the most common choice, covers 80% of use cases
- Document the embedding model clearly in API responses

**Post-MVP: "Bring Your Own Embeddings" (BYOE):**
```python
# Option 1: Get pre-computed (default)
chunk = client.get_chunk("nvda-10k-2024-risk-007")
print(chunk.embedding)  # Our pre-computed OpenAI embedding

# Option 2: Get text only, embed yourself
chunk = client.get_chunk("nvda-10k-2024-risk-007", include_embedding=False)
# User embeds with their own model

# Option 3 (Future): Request specific embedding
chunk = client.get_chunk(
    "nvda-10k-2024-risk-007",
    embedding_model="cohere-embed-v3"  # We generate on-demand
)
```

**API Response Transparency:**
```json
{
    "embedding": [0.12, -0.34, ...],
    "embedding_metadata": {
        "model": "text-embedding-3-small",
        "dimensions": 1536,
        "generated_at": "2024-10-15T00:00:00Z"
    }
}
```

---

### Challenge 3: Caching Architecture (No SEC Proxy!) 🟡 MEDIUM

**The Problem:**
SEC EDGAR strictly enforces 10 requests/second and **bans IPs** that violate it. If 100 users hit our API and we proxy calls to SEC in real-time, we get banned.

**The Solution: Database is Source of Truth**

```
┌─────────────────────────────────────────────────────────────────┐
│                    CACHING ARCHITECTURE                          │
│                                                                  │
│   User Request                                                   │
│        │                                                         │
│        ▼                                                         │
│   ┌─────────┐                                                    │
│   │  API    │──→ Check Redis Cache (hot data, TTL: 5 min)       │
│   │ Gateway │                                                    │
│   └────┬────┘                                                    │
│        │ Cache Miss                                              │
│        ▼                                                         │
│   ┌─────────────┐                                                │
│   │ PostgreSQL  │──→ Query our database (SOURCE OF TRUTH)       │
│   │ + VectorDB  │                                                │
│   └─────────────┘                                                │
│                                                                  │
│   ═══════════════════════════════════════════════════════════   │
│                                                                  │
│   Background Job (NEVER user-triggered):                        │
│                                                                  │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│   │  Scheduler  │────▶│ SEC Scraper │────▶│  Database   │       │
│   │  (Cron)     │     │ (10 req/sec)│     │  Ingestion  │       │
│   └─────────────┘     └─────────────┘     └─────────────┘       │
│                                                                  │
│   - Runs nightly for incremental updates                        │
│   - Full backfill runs once during setup                        │
│   - User requests NEVER hit SEC directly                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Key Principles:**
1. **All user requests hit our database, never SEC**
2. SEC scraping is batch, scheduled, rate-limited
3. New filings available within 24 hours (acceptable for most use cases)
4. If real-time is needed (future), we use SEC's RSS feed + queue

---

### Challenge 4: MVP Scope Control 🟢 LOW RISK

**The Trap:** Trying to ingest the entire S&P 500 immediately

**The Solution: Vertical Slice First**

**MVP Focus: Technology/SaaS Companies (50-100 companies)**

Why this vertical:
- You understand the domain (FDD background)
- Clear metrics to extract (ARR, Churn, NRR mentioned in MD&A)
- Active developer community building fintech tools
- Representative complexity (tables, XBRL, narrative)

**MVP Company List:**
```
Tier 1 (Must Have - 20 companies):
AAPL, MSFT, GOOGL, AMZN, META, NVDA, TSLA, CRM, ADBE, ORCL,
INTC, AMD, CSCO, IBM, NOW, SNOW, PLTR, UBER, ABNB, SQ

Tier 2 (Should Have - 30 companies):
[Other major tech companies]

Tier 3 (Nice to Have - 50 companies):
[Broader tech/SaaS universe]
```

**Expansion Path:**
```
MVP:        Tech/SaaS (100 companies)
Month 3:    S&P 500 (500 companies)
Month 6:    Russell 1000 (1,000 companies)
Month 12:   All public companies (5,000+)
```

---

## Go-to-Market Strategy

### Phase 1: Developer Love (Months 1-6)

**Goal:** 1,000 free users, 100 beta testers, product-market fit signal

**Tactics:**

1. **Launch on Hacker News**
   - "Show HN: LLM-native SEC data API with citations"
   - Target: 200 signups in first week

2. **Developer Content Marketing**
   - Blog: "Building a Financial Research Agent with Claude and Our API"
   - Tutorial: "RAG for SEC Filings in 10 Minutes"
   - GitHub: Sample applications and notebooks

3. **Community Engagement**
   - r/algotrading, r/quantfinance, r/MachineLearning
   - Twitter/X: Financial AI builder community
   - Discord: Support channel + community

4. **Partnerships**
   - Integration with LangChain, LlamaIndex
   - Featured in AI framework documentation

**Metrics:**
- Signups: 1,000
- WAU (Weekly Active Users): 200
- API calls/week: 50,000
- NPS: >50

### Phase 2: Product-Led Growth (Months 6-12)

**Goal:** 100 paying customers, $10k MRR

**Tactics:**

1. **Freemium Conversion Optimization**
   - In-product upgrade prompts at usage limits
   - Feature gates (historical data, embeddings)
   - Annual discount (20% off)

2. **Self-Serve Expansion**
   - Team plans with shared billing
   - Usage-based pricing for high-volume users
   - Enterprise inquiry form

3. **Developer Advocacy**
   - Identify power users as champions
   - Case studies and testimonials
   - Referral program (1 month free)

**Metrics:**
- Paying customers: 100
- MRR: $10k
- Conversion rate (free → paid): 10%
- Churn: <5% monthly

### Phase 3: Enterprise Expansion (Months 12-24)

**Goal:** 10 enterprise customers, $500k ARR

**Tactics:**

1. **Enterprise Product**
   - SSO/SAML integration
   - Audit logs and compliance
   - SLAs and dedicated support
   - Disclosure formatting UI (Year 2 product)

2. **Sales-Assisted Motion**
   - PLG-qualified leads (high usage free users)
   - Outbound to PwC/Big 4 contacts
   - Industry conferences (FPA, AICPA)

3. **Strategic Partnerships**
   - White-label for financial software vendors
   - Integration with Bloomberg alternatives
   - Academic partnerships

**Metrics:**
- Enterprise customers: 10
- ARR: $500k
- ACV (Average Contract Value): $30-50k
- Sales cycle: <90 days

---

## Implementation Roadmap

### Phase 1: MVP (Weeks 1-8)

#### Week 1-2: Foundation
- [ ] Set up monorepo structure
- [ ] Configure CI/CD (GitHub Actions)
- [ ] Deploy infrastructure (Railway/Render)
- [ ] Set up PostgreSQL and ChromaDB
- [ ] Implement authentication (API keys)

#### Week 3-4: Ingestion Pipeline
- [ ] Migrate existing EdgarClient from sec-edgar-agent
- [ ] Build semantic chunker (context-aware, ~500 tokens)
- [ ] Implement citation generator
- [ ] Create embedding pipeline (OpenAI/local model)
- [ ] Build basic tagger (section types, form types)

#### Week 5-6: Core API
- [ ] `/v1/search` - semantic search endpoint
- [ ] `/v1/filings/{id}` - filing metadata
- [ ] `/v1/companies/{ticker}` - company info
- [ ] `/v1/chunks/{id}` - chunk detail
- [ ] Rate limiting and usage tracking

#### Week 7-8: Developer Experience
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Python SDK v0.1
- [ ] Quick start guide
- [ ] Sample Jupyter notebooks
- [ ] Landing page and signup flow

**MVP Deliverables:**
- Working API with 4 core endpoints
- 5 years of 10-K/10-Q data for **Tech/SaaS vertical (100 companies)**
- Python SDK
- Basic documentation

> **Scope Note:** Start narrow with tech companies where we understand the domain. Expand to S&P 500 in Month 3 after validating the core pipeline.

### Phase 2: Beta (Weeks 9-16)

#### Week 9-10: Data Expansion
- [ ] Process full S&P 500 historical data
- [ ] Add 8-K (event) filings
- [ ] Add Form 4 (insider) filings
- [ ] Implement incremental daily updates

#### Week 11-12: Enhanced Features
- [ ] `/v1/financials` - standardized financial data
- [ ] `/v1/compare` - cross-filing comparison
- [ ] Advanced semantic tagging (ASC topics, risk types)
- [ ] JavaScript/TypeScript SDK

#### Week 13-14: Developer Tools
- [ ] Interactive API explorer
- [ ] Webhook support for new filings
- [ ] Usage dashboard
- [ ] Billing integration (Stripe)

#### Week 15-16: Beta Launch
- [ ] Private beta with 50-100 users
- [ ] Feedback collection and iteration
- [ ] Performance optimization
- [ ] Documentation refinement

**Beta Deliverables:**
- Full S&P 500 + Russell 1000 coverage
- 6 API endpoints
- Python and JavaScript SDKs
- Stripe billing integration
- 100 beta users

### Phase 3: Production (Weeks 17-24)

#### Week 17-18: Reliability
- [ ] Multi-region deployment
- [ ] Automated failover
- [ ] Comprehensive monitoring
- [ ] Incident response procedures

#### Week 19-20: Scale
- [ ] Migrate to Pinecone (if needed)
- [ ] Implement request queuing
- [ ] CDN for static assets
- [ ] Database read replicas

#### Week 21-22: Enterprise Prep
- [ ] SSO integration
- [ ] Audit logging
- [ ] Team management
- [ ] SLA documentation

#### Week 23-24: Public Launch
- [ ] Hacker News launch
- [ ] Product Hunt launch
- [ ] Press/PR outreach
- [ ] Launch promotions

**Production Deliverables:**
- 99.9% uptime SLA
- <200ms p95 latency
- Enterprise features
- Public launch

### Phase 4: Growth (Months 7-12)

- [ ] Temporal analysis features
- [ ] Relationship graphs
- [ ] Custom tagging API
- [ ] Disclosure formatting UI (enterprise)
- [ ] International expansion (IFRS)

---

## Business Model

### Pricing Strategy

> **Pricing Philosophy:** Financial data has high price inelasticity. A developer building a trading bot or risk tool will pay $249 just as easily as $99 if the data is clean. **Don't race to the bottom on price; race to the top on data cleanliness.**

**Freemium Model (PLG-Optimized)**

| Tier | Price | Limits | Target |
|------|-------|--------|--------|
| **Hobby** | $0 | 500 calls/mo, 1 year data, no embeddings, 10 companies | Students, evaluators |
| **Pro** | $249/mo | 50,000 calls/mo, 5 years data, embeddings, all companies | Individual developers, small projects |
| **Team** | $499/mo | 200,000 calls/mo, full history, embeddings, 5 seats | Startups, small funds |
| **Enterprise** | Custom ($2k+/mo) | Unlimited, SLA, SSO, dedicated support, custom integrations | Large organizations |

**Why Higher Pricing:**
- $249/mo is still **96% cheaper** than AlphaSense ($10k+/seat)
- Clean, LLM-ready data saves developers 40+ hours of engineering
- Financial buyers have budget - don't leave money on the table

**Usage-Based Overages**
- Additional API calls: $0.005/call
- On-demand embedding generation: $0.0002/embedding
- Priority support: $500/mo add-on

### Unit Economics (Target)

| Metric | Target | Notes |
|--------|--------|-------|
| Gross Margin | 85% | Infrastructure efficient |
| CAC (Customer Acquisition Cost) | $100 | PLG minimizes sales cost |
| LTV (Lifetime Value) | $5,976 | 2-year average retention @ $249/mo |
| LTV:CAC Ratio | 60:1 | Highly efficient |
| Payback Period | <1 month | Fast value realization |
| ARPU (Monthly) | $249-350 | Blend of Pro + Team |

### Revenue Projections (Updated Pricing)

| Timeframe | Hobby Users | Paid Users | Avg Price | MRR | ARR |
|-----------|-------------|------------|-----------|-----|-----|
| Month 6 | 500 | 20 | $280 | $5,600 | $67,200 |
| Month 12 | 1,000 | 80 | $300 | $24,000 | $288,000 |
| Month 18 | 2,000 | 150 | $320 | $48,000 | $576,000 |
| Month 24 | 3,000 | 250 | $350 | $87,500 | $1,050,000 |

*Note: Higher pricing means fewer but higher-quality customers. Avg price increases as Team tier gains adoption.*

---

## Competitive Analysis

### Direct Competitors

| Competitor | Strengths | Weaknesses | Our Advantage |
|------------|-----------|------------|---------------|
| **sec-api.io** | Established, full EDGAR coverage | Text-only, not LLM-optimized | LLM-native architecture |
| **Intrinio** | Standardized data, ML-processed | Enterprise sales, expensive | Self-serve, 10x cheaper |
| **Captide** | RAG-focused | Limited documentation, new | Better DX, more features |
| **Kay.ai** | Embeddings API | Limited to embeddings | Full-stack solution |

### Indirect Competitors

| Competitor | When They Win | Our Counter |
|------------|---------------|-------------|
| **Bloomberg** | Enterprise needs terminal + data | We're complementary for AI use cases |
| **AlphaSense** | Need broad content (transcripts, research) | We specialize in SEC filings |
| **Hebbia** | Enterprise document analysis | We're API-first for builders |
| **DIY Solutions** | Technical teams with time | We save 100+ hours of engineering |

### Competitive Moats (Planned)

1. **Data Quality Moat** - Semantic chunking, citation accuracy, temporal tracking
2. **Developer Experience Moat** - Best docs, fastest integration, most helpful support
3. **Network Effects** - More users → more feedback → better product
4. **Switching Costs** - Deep integration into customer workflows

---

## Risk Assessment

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| SEC rate limiting | Medium | High | Distributed scraping, caching |
| Embedding model changes | Medium | Medium | Abstract embedding layer, multiple providers |
| Scale bottlenecks | Medium | High | Load testing, architecture review |
| Data quality issues | High | High | Automated QA, user feedback loops |

### Business Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Competitor copies features | High | Medium | Move fast, build community |
| Enterprise sales slow | Medium | Medium | PLG as primary motion |
| SEC changes data access | Low | High | Monitor policy, diversify sources |
| Economic downturn | Medium | Medium | Focus on cost-conscious buyers |

### Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Founder burnout | Medium | High | Sustainable pace, clear milestones |
| Key person dependency | High | High | Document everything, hire early |
| Security breach | Low | Critical | Security audit, encryption, monitoring |

---

## Success Metrics

### North Star Metric

**Weekly Active API Calls** - Measures actual usage and value delivery

### Primary Metrics

| Metric | Month 6 Target | Month 12 Target |
|--------|----------------|-----------------|
| Weekly Active Users (WAU) | 200 | 500 |
| Weekly API Calls | 50,000 | 500,000 |
| Paying Customers | 20 | 100 |
| MRR | $2,000 | $10,000 |
| NPS | >40 | >50 |

### Secondary Metrics

| Metric | Target | Purpose |
|--------|--------|---------|
| Time to First API Call | <10 min | Onboarding quality |
| Documentation Rating | >4.5/5 | DX quality |
| API Latency (p95) | <200ms | Performance |
| Uptime | 99.9% | Reliability |
| Support Response Time | <4 hours | Customer success |

### Health Metrics

| Metric | Healthy Range | Alert Threshold |
|--------|---------------|-----------------|
| Free → Paid Conversion | 5-15% | <3% |
| Monthly Churn | <5% | >8% |
| API Error Rate | <0.1% | >1% |
| Customer Satisfaction | >4/5 | <3.5/5 |

---

## Open Questions

### Product Questions

- [ ] What embedding model to use? (OpenAI vs. open-source)
- [ ] How to handle international filings (IFRS, local GAAP)?
- [ ] Should we offer a managed RAG solution or just the data layer?
- [ ] What level of financial standardization is sufficient for MVP?

### Technical Questions

- [ ] ChromaDB vs. Pinecone vs. Weaviate for production?
- [ ] How to handle SEC filing format changes over time?
- [ ] What's the right chunking strategy for tables vs. narrative?
- [ ] How to scale embedding generation cost-effectively?

### Business Questions

- [ ] Bootstrap or seek funding?
- [ ] What's the right free tier limit to drive conversion?
- [ ] When to hire first employee?
- [ ] How to price enterprise tier?

### Validation Questions (Pre-Build)

- [ ] **Week 1:** Talk to 10 potential users - would they pay $249/mo?
- [ ] **Week 2:** Technical spike - can we chunk filings with citation accuracy?
- [ ] **Week 3:** Competitive trial - what exactly does sec-api.io not do?
- [ ] **Week 4:** Landing page test - can we get 100 waitlist signups?

---

## Immediate Next Steps

> **"Stop planning and solve the Table Problem."** - Gemini

### This Week: Table Parsing POC

**The Test:** Create a Python script that takes a complex Apple (AAPL) 10-K HTML table and converts it into a format an LLM can accurately read.

**Target Table:** Apple's Segment Information from latest 10-K
- Multi-level headers (Region → Metric)
- Multiple years (2022, 2023, 2024)
- Nested structure with subtotals

**Success Criteria:**
1. [ ] Parse table with 100% numeric accuracy
2. [ ] Output in Markdown format
3. [ ] Feed to Claude/GPT-4 and ask "What was Americas operating income in 2024?"
4. [ ] Model answers correctly with high confidence
5. [ ] Citation preserved (file, page, table location)

**Implementation Plan:**

```bash
# Day 1: Set up environment
pip install sec-parser edgartools pandas beautifulsoup4

# Day 2: Download Apple 10-K, identify target table
python scripts/fetch_aapl_10k.py

# Day 3-4: Implement table parser
# Try sec-parser first, fall back to custom solution

# Day 5: Validate with LLM
# Feed parsed output to Claude, measure accuracy
```

**If This Works:** We have a business. Proceed to MVP.
**If This Fails:** Need to research alternatives (LayoutLM, vision models) or scope down.

### Next 4 Weeks: Validation Sprint

| Week | Focus | Deliverable |
|------|-------|-------------|
| 1 | **Table POC** | Working parser for AAPL segment table |
| 2 | **User Research** | 10 interviews, pricing validation |
| 3 | **Competitive Analysis** | sec-api.io trial, gap analysis |
| 4 | **Landing Page** | Waitlist with 100 signups |

**Go/No-Go Decision (End of Week 4):**
- [ ] Table parsing works reliably
- [ ] 5+ users said "yes, I'd pay $249/mo"
- [ ] Clear differentiation from sec-api.io documented
- [ ] 100+ waitlist signups

If all boxes checked → Start MVP build
If not → Reassess or pivot

---

## Changelog

| Date | Author | Changes |
|------|--------|---------|
| 12/10/2025 05:23 PM PST | Claude/Wolfgang | Initial document creation |
| 12/10/2025 05:34 PM PST | Claude/Wolfgang | Incorporated Gemini feedback: Added "Killer Features" section highlighting temporal diff as key differentiator; Added "Critical Technical Challenges" section addressing HTML table parsing, embedding rot/BYOE, and caching architecture; Updated pricing ($249 Pro, $499 Team) based on price inelasticity insight; Pivoted "Standardized Financials" to "XBRL Tag Extraction"; Narrowed MVP scope to Tech/SaaS vertical slice (100 companies); Added "Immediate Next Steps" with Table Parsing POC as critical validation |

---

## Appendices

### A. Reference Links

**Market Research:**
- [Plaid Business Breakdown](https://research.contrary.com/company/plaid/)
- [LLM in Finance Market](https://appinventiv.com/blog/large-language-models-in-finance/)
- [RAG in Financial Services](https://hatchworks.com/blog/gen-ai/rag-for-financial-services/)

**Technical Resources (Table Parsing - Critical):**
- [sec-parser](https://github.com/alphanome-ai/sec-parser) - Purpose-built SEC EDGAR HTML parser
- [sec-parser Documentation](https://sec-parser.readthedocs.io/en/stable/notebooks/user_guide.html)
- [EdgarTools XBRL Guide](https://edgartools.readthedocs.io/en/latest/getting-xbrl/)
- [LayoutLM (Hugging Face)](https://huggingface.co/docs/transformers/model_doc/layoutlm) - Fallback for complex tables

**Technical Resources (Infrastructure):**
- [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
- [Vector Database Comparison](https://aloa.co/ai/comparisons/vector-database-comparison/pinecone-vs-weaviate-vs-chroma)
- [Stripe Documentation Standards](https://devdocs.work/post/stripe-twilio-achieving-growth-through-cutting-edge-documentation)

**Competitive Intelligence:**
- [sec-api.io Pricing](https://sec-api.io/pricing)
- [Intrinio](https://intrinio.com)
- [AlphaSense](https://www.alpha-sense.com/)

### B. Existing Assets (from sec-edgar-agent)

**Reusable Components:**
- `src/data/edgar_client.py` - SEC API wrapper with rate limiting
- `src/data/vector_store.py` - ChromaDB semantic search
- `src/utils/citations.py` - Citation generation
- `src/tools/registry.py` - Tool patterns for API design

**Patterns to Preserve:**
- Citation format: `[TICKER FORM YEAR, Section, Page]`
- Rate limiting: 10 req/sec to SEC
- XBRL parsing for financials
- Semantic search architecture

### C. Name Ideas

**Product Names:**
- Edgar API
- FinDocs API
- SECBase
- FilingIQ
- Disclosure.dev

**Company Names:**
- Disclosure Labs
- Filing Intelligence
- SECData.io
- FinRAG

---

*This is a living document. Update as decisions are made and learnings emerge.*
