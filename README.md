# SEC EDGAR Agent for LLMs

An AI-native platform for financial research, providing LLM-ready SEC filing data with structured tables, semantic search, and RAG capabilities.

## 🚀 Features

- **Semantic Search**: Search across SEC listings using natural language (powered by OpenAI embeddings and ChromaDB).
- **RAG Chat**: Ask questions about financial filings and get answers with **citations** (e.g., `[AAPL 10-K, Item 8]`).
- **Structured Tables**: 100% accurate table extraction converted to LLM-friendly Markdown, preserving logical structure.
- **Robust Ingestion**: Asynchronous pipeline to index filings with state tracking and idempotency.
- **Python SDK**: Developer-friendly client (`sec-api-llm`) for easy integration.

## 🛠️ Architecture

The system is built as a modular microservices-ready application:

- **API**: FastAPI service handling requests.
- **Vector Store**: ChromaDB for embedding and retrieving filing chunks.
- **Database**: SQLite (SQLModel) for tracking ingestion job state.
- **Parser**: Specialized logic for extracting tables and content from EDGAR HTML.
- **SDK**: A typed Python client for interacting with the API.

## 🏁 Quick Start

### Using Docker (Recommended)

1.  **Set Environment Variables**:
    Create a `.env` file (or set variables directly):

    ```bash
    OPENAI_API_KEY=sk-...    # Required for Search/Chat
    SEC_USER_AGENT="Name email@example.com"
    API_KEY=sec-api-demo    # For ingestion endpoints
    ```

    `sec-api-demo` is for local development only. Production deployments must
    set `ENVIRONMENT=production` and provide a non-default `API_KEY`; otherwise
    the API refuses to start.

2.  **Run with Docker Compose**:
    ```bash
    docker-compose up --build
    ```
    The API will be available at `http://localhost:8000`.

### Local Development

1.  **Install `uv`**:

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

2.  **Install Dependencies**:

    ```bash
    uv sync
    ```

3.  **Run the Server**:
    ```bash
    export OPENAI_API_KEY=sk-...
    uv run uvicorn src.api.main:app --reload
    ```

## 📦 Python SDK

This project includes a Python SDK for easy interaction.

### Installation

```bash
cd sdk
pip install -e .
```

### Usage Example

```python
from sec_api_llm import SecClient

client = SecClient(base_url="http://localhost:8000/api/v1")

# 1. Trigger Ingestion (Async)
job = client.ingest.trigger(ticker="AAPL", form_type="10-K", year=2024)
print(f"Job started: {job['job_id']}")

# ... wait for job completion ...

# 2. Semantic Search
results = client.search.query("What are the risk factors?")
for res in results.results:
    print(res.content)

# 3. Chat with Citations
response = client.chat.create(
    messages=[{"role": "user", "content": "What was the net income?"}],
    ticker="AAPL"
)
print(response.answer)
# Output: "The net income was $97B [AAPL 10-K, Item 8]."
```

## 📚 API Reference

| Method | Endpoint               | Description                            |
| ------ | ---------------------- | -------------------------------------- |
| `POST` | `/api/v1/search`       | Semantic search over indexed filings   |
| `POST` | `/api/v1/chat`         | RAG chat with context and citations    |
| `POST` | `/api/v1/ingest`       | Trigger background ingestion job       |
| `GET`  | `/api/v1/ingest/{id}`  | Get ingestion job status               |
| `POST` | `/api/v1/tables/parse` | Extract structured tables from filings |
| `GET`  | `/api/v1/filings/...`  | Get filing metadata                    |

## 🧪 Testing

Run unit tests:

```bash
uv run pytest
```

Run the end-to-end demo script:

```bash
uv run python scripts/demo_tier1.py
```

## 📄 License

MIT
