"""Request payloads for the public API."""
from typing import Any

from pydantic import BaseModel, Field


class TableParseRequest(BaseModel):
    """Request to parse a specific table from a filing."""
    ticker: str = Field(..., json_schema_extra={"example": "AAPL"}, description="Stock ticker symbol")
    form_type: str = Field(..., json_schema_extra={"example": "10-K"}, description="SEC form type (e.g., 10-K, 10-Q)")
    year: int = Field(..., json_schema_extra={"example": 2024}, ge=2000, le=2030)
    table_name: str = Field(
        ...,
        json_schema_extra={"example": "income_statement"},
        description="Target table: 'balance_sheet', 'income_statement', 'cash_flow', or 'segment_information'."
    )


class SearchRequest(BaseModel):
    """Semantic search request body."""
    query: str = Field(..., json_schema_extra={"example": "What are the risk factors?"}, description="Natural language query")
    ticker: str | None = Field(None, json_schema_extra={"example": "AAPL"}, description="Filter by ticker")
    section: str | None = Field(None, json_schema_extra={"example": "Item 1A"}, description="Filter by section")
    limit: int = Field(5, ge=1, le=20, description="Max results")


class IngestRequest(BaseModel):
    """Request to trigger a filing ingestion job."""
    ticker: str = Field(..., json_schema_extra={"example": "AAPL"}, description="Stock ticker symbol")
    form_type: str = Field(..., json_schema_extra={"example": "10-K"}, description="SEC form type")
    year: int = Field(..., json_schema_extra={"example": 2024}, ge=2000, le=2030)


class ChatMessage(BaseModel):
    """Single chat message for the orchestrator."""
    role: str = Field(..., description="user or assistant")
    content: str

class ChatRequest(BaseModel):
    """Chat session containing prior messages."""
    messages: list[ChatMessage]
    ticker: str | None = None
    stream: bool = False

class ChatResponse(BaseModel):
    """Response payload for chat endpoints."""
    answer: str
    citations: list[str]
    usage: dict[str, Any] = {}


class QueryRequest(BaseModel):
    """Request to start a query session."""
    query: str | None = None


class QueryResponse(BaseModel):
    """Response for query session start."""
    query_id: str
    status: str
