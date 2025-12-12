from typing import Any

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., description="The natural language query to process")

class QueryResponse(BaseModel):
    query_id: str = Field(..., description="Unique identifier for the query session")
    status: str = Field(..., description="Current status of the query (e.g., 'started')")

class ToolParameter(BaseModel):
    name: str
    type: str
    description: str | None = None
    required: bool = False

class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]

class ToolListResponse(BaseModel):
    tools: list[ToolDefinition]

class ToolExecutionRequest(BaseModel):
    arguments: dict[str, Any] = Field(..., description="Arguments to pass to the tool")

class ToolExecutionResponse(BaseModel):
    success: bool
    result: Any
    error: str | None = None
    citations: list[str] = Field(default_factory=list)
