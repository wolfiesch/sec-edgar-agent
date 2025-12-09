# SEC EDGAR Financial Agent

An autonomous AI agent for financial research using SEC EDGAR filings.

## Features

- **Direct SEC Access**: Free access to SEC EDGAR APIs with no commercial dependencies
- **Citation-Backed**: Every response includes citations to source filings
- **Rich CLI**: Beautiful terminal interface with tables and formatting
- **Tool-Based Architecture**: Extensible tool registry for AI agent integration

## Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/sec-edgar-agent.git
cd sec-edgar-agent

# Install dependencies with uv
uv sync

# Copy environment file and add your API key
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY

# Run the agent
uv run edgar-agent
```

## Usage

### Interactive Mode

```bash
uv run edgar-agent
```

Available commands:
- `/company AAPL` - Get company info
- `/filings AAPL` - List recent filings
- `/financials AAPL` - Get financial data
- `/insider AAPL` - Get insider trading activity
- `/help` - Show all commands

### CLI Commands

```bash
# Get company info
uv run edgar-agent company AAPL

# List filings
uv run edgar-agent filings AAPL --form 10-K --limit 5

# Get financials
uv run edgar-agent financials AAPL --periods 3
```

## Architecture

```
User Query → Tool Registry → SEC EDGAR API → Response with Citations
```

### Key Components

- **Tool Registry** (`src/tools/registry.py`): Registers tools for Claude's tool_use API
- **Edgar Client** (`src/data/edgar_client.py`): Wraps edgartools with rate limiting
- **Tools** (`src/tools/`): Search, fetch, and financial data extraction

## SEC EDGAR Notes

- **Rate Limit**: SEC requires max 10 requests/second
- **User Agent**: SEC requires identification via User-Agent header
- **Free API**: No authentication required for `data.sec.gov`

## Development

```bash
# Run tests
uv run pytest

# Type checking
uv run mypy src/

# Linting
uv run ruff check src/
uv run ruff format src/
```

## License

MIT
