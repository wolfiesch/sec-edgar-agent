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
