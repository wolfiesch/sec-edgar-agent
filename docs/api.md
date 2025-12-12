# API Documentation

The SEC EDGAR Agent provides a REST API for accessing financial data, managing ingestion, and performing semantic search.

## Base URL

`http://localhost:8000/api/v1`

## Authentication

Ingestion endpoints require an API Key header:
`X-API-Key: <your_api_key>` (Default: `sec-api-demo`)

Search and Public Filing endpoints are open, but may be rate-limited.

## Endpoints

### 🔍 Search & Chat

#### `POST /search`

Semantic search over indexed filings.

**Request:**

```json
{
  "query": "What are the risks?",
  "ticker": "AAPL",
  "limit": 5
}
```

**Response:**

```json
{
  "query": "What are the risks?",
  "results": [
    {
      "content": "Risk factors include...",
      "metadata": { "ticker": "AAPL", "section_name": "Item 1A" },
      "score": 0.85
    }
  ]
}
```

#### `POST /chat`

RAG-enabled chat with citations.

**Request:**

```json
{
  "messages": [{ "role": "user", "content": "Net income for 2024?" }],
  "ticker": "AAPL"
}
```

**Response:**

```json
{
  "answer": "The net income was...",
  "citations": ["[AAPL 10-K, Item 8]"],
  "usage": {}
}
```

### 📥 Ingestion

#### `POST /ingest`

Trigger a background ingestion job.

**Request:**

```json
{
  "ticker": "AAPL",
  "form_type": "10-K",
  "year": 2024
}
```

**Response:**

```json
{
  "company": "Apple Inc.",
  "status": "triggered",
  "job_id": 123
}
```

#### `GET /ingest/{job_id}`

Check job status.

**Response:**

```json
{
  "job_id": 123,
  "ticker": "AAPL",
  "status": "DONE",
  "created_at": "...",
  "completed_at": "..."
}
```

### 📄 Tables

#### `POST /tables/parse`

Extract structured tables from filings.

**Request:**

```json
{
  "ticker": "AAPL",
  "form_type": "10-K",
  "table_name": "segment_information",
  "year": 2024
}
```

**Response:**

```json
{
  "markdown": "| Segment | Sales |...",
  "structured": [{ "Segment": "Americas", "Sales": 100 }],
  "citation": "[AAPL 10-K, Item 8]"
}
```

### 📁 Filings

#### `GET /filings/{ticker}/{form_type}`

Get filing metadata.
