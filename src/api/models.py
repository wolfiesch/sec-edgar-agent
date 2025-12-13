"""Shared API models for tool discovery and execution endpoints."""
from typing import Any

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Payload for starting a new natural-language query."""
    query: str = Field(..., description="The natural language query to process")

class QueryResponse(BaseModel):
    """Response with a handle for polling or streaming results."""
    query_id: str = Field(..., description="Unique identifier for the query session")
    status: str = Field(..., description="Current status of the query (e.g., 'started')")

class ToolParameter(BaseModel):
    """Description of a single tool parameter."""
    name: str
    type: str
    description: str | None = None
    required: bool = False

class ToolDefinition(BaseModel):
    """Metadata describing an available tool."""
    name: str
    description: str
    parameters: dict[str, Any]

class ToolListResponse(BaseModel):
    """Collection of tool definitions returned by the listing endpoint."""
    tools: list[ToolDefinition]

class ToolExecutionRequest(BaseModel):
    """Arguments wrapper used when invoking a tool."""
    arguments: dict[str, Any] = Field(..., description="Arguments to pass to the tool")

class ToolExecutionResponse(BaseModel):
    """Standardized execution result returned to API clients."""
    success: bool
    result: Any
    error: str | None = None
    citations: list[str] = Field(default_factory=list)
