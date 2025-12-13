"""Tool-related Pydantic models."""
from typing import Any

from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
    """Definition of an available tool."""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Tool parameters schema")


class ToolListResponse(BaseModel):
    """Response containing list of available tools."""
    tools: list[ToolDefinition]


class ToolExecutionRequest(BaseModel):
    """Request to execute a tool."""
    arguments: dict[str, Any] = Field(default_factory=dict, description="Tool arguments")


class ToolExecutionResponse(BaseModel):
    """Response from tool execution."""
    success: bool
    result: Any
    error: str | None = None
    citations: list[str] = Field(default_factory=list)
