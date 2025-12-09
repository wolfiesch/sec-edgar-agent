from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from src.api.models import ToolListResponse, ToolDefinition, ToolExecutionRequest, ToolExecutionResponse
from src.tools.registry import registry

router = APIRouter()

@router.get("", response_model=ToolListResponse)
async def list_tools():
    """List all available tools."""
    tools = []
    # registry._tools is a dict of ToolDefinition objects (internal)
    # We map them to our API model
    for name, tool in registry._tools.items():
        tools.append(ToolDefinition(
            name=name,
            description=tool.description,
            parameters=tool.parameters
        ))
    return ToolListResponse(tools=tools)

@router.post("/{tool_name}", response_model=ToolExecutionResponse)
async def execute_tool(tool_name: str, request: ToolExecutionRequest):
    """Execute a specific tool."""
    tool = registry.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    result = registry.execute(tool_name, request.arguments)
    
    return ToolExecutionResponse(
        success=result.success,
        result=result.result,
        error=result.error,
        citations=[str(c) for c in result.citations]
    )
