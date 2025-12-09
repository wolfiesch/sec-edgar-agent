from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    query: str = Field(..., description="The natural language query to process")

class QueryResponse(BaseModel):
    query_id: str = Field(..., description="Unique identifier for the query session")
    status: str = Field(..., description="Current status of the query (e.g., 'started')")

class ToolParameter(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    required: bool = False

class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]

class ToolListResponse(BaseModel):
    tools: List[ToolDefinition]

class ToolExecutionRequest(BaseModel):
    arguments: Dict[str, Any] = Field(..., description="Arguments to pass to the tool")

class ToolExecutionResponse(BaseModel):
    success: bool
    result: Any
    error: Optional[str] = None
    citations: List[str] = Field(default_factory=list)
