from pydantic import BaseModel, Field


class TableParseRequest(BaseModel):
    """Request to parse a specific table from a filing."""
    ticker: str = Field(..., json_schema_extra={"example": "AAPL"}, description="Stock ticker symbol")
    form_type: str = Field(..., json_schema_extra={"example": "10-K"}, description="SEC form type (e.g., 10-K, 10-Q)")
    year: int = Field(..., json_schema_extra={"example": 2024}, ge=2000, le=2030)
    table_name: str = Field(
        ...,
        json_schema_extra={"example": "segment_information"},
        description="Target table name/description. For 'segment_information', uses 'segment table' logic."
    )


class SearchRequest(BaseModel):
    query: str = Field(..., json_schema_extra={"example": "What are the risk factors?"}, description="Natural language query")
    ticker: str | None = Field(None, json_schema_extra={"example": "AAPL"}, description="Filter by ticker")
    section: str | None = Field(None, json_schema_extra={"example": "Item 1A"}, description="Filter by section")
    limit: int = Field(5, ge=1, le=20, description="Max results")


class IngestRequest(BaseModel):
    ticker: str = Field(..., json_schema_extra={"example": "AAPL"}, description="Stock ticker symbol")
    form_type: str = Field(..., json_schema_extra={"example": "10-K"}, description="SEC form type")
    year: int = Field(..., json_schema_extra={"example": 2024}, ge=2000, le=2030)


class ChatMessage(BaseModel):
    role: str = Field(..., description="user or assistant")
    content: str

class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    ticker: str | None = None
    stream: bool = False

class ChatResponse(BaseModel):
    answer: str
    citations: list[str]
    usage: dict[str, int] = {}
