# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SEC EDGAR Financial Agent - An autonomous AI agent for financial research using SEC EDGAR filings. Uses Claude for reasoning and edgartools for SEC data access.

## Commands

```bash
# Install dependencies
uv sync

# Run the CLI
uv run edgar-agent

# Run tests
uv run pytest

# Run single test
uv run pytest tests/test_tools/test_search.py -k "test_name"

# Type checking
uv run mypy src/

# Linting
uv run ruff check src/
uv run ruff format src/
```

## Architecture

```
User Query → Orchestrator → Planner Agent → Tool Selection → Executor Agent → Validator → Response
```

### Key Components

- **Orchestrator** (`src/agents/orchestrator.py`): Coordinates multi-agent workflow with loop detection
- **Tool Registry** (`src/tools/registry.py`): Registers tools for Claude's tool_use API
- **EdgarClient** (`src/data/edgar_client.py`): Wraps edgartools with rate limiting (10 req/sec SEC limit)
- **Citations** (`src/utils/citations.py`): Generates `[TICKER FORM YEAR, Section, Page]` references

### Data Flow

1. EdgarClient fetches filings → cached 30 min
2. Tools extract structured data (XBRL for financials)
3. Vector store (ChromaDB) indexes sections for semantic search
4. Every response includes citation to source filing

## SEC EDGAR Specifics

- Rate limit: 10 requests/second (enforced in `rate_limiter.py`)
- User-Agent header required by SEC (configured in .env)
- Free API, no auth: `data.sec.gov`
- Key forms: 10-K (annual), 10-Q (quarterly), 8-K (events), Form 4 (insider)

## Adding New Tools

1. Create function in `src/tools/`
2. Decorate with `@registry.register()` including JSON schema
3. Tool auto-available to Claude via `registry.get_tools_for_llm()`
