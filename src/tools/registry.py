"""Tool registry for SEC EDGAR Agent.

Provides a decorator-based system for registering tools that can be
used by the Claude API's tool_use feature.
"""

import logging
import time
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar

from pydantic import BaseModel

from src.data.models import Citation, ToolResult

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


class ToolDefinition(BaseModel):
    """Definition of a registered tool."""

    name: str
    description: str
    parameters: dict[str, Any]
    function: Callable[..., Any] | None = None

    class Config:
        arbitrary_types_allowed = True


class ToolRegistry:
    """
    Registry for tools available to the AI agent.

    Tools are registered with JSON Schema parameters for Claude's tool_use.
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """
        Decorator to register a tool.

        Args:
            name: Unique tool name
            description: Tool description for the LLM
            parameters: JSON Schema for tool parameters

        Example:
            @registry.register(
                name="search_filings",
                description="Search SEC filings for a company",
                parameters={
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string", "description": "Stock ticker"},
                        "form_type": {"type": "string", "description": "Form type"}
                    },
                    "required": ["ticker"]
                }
            )
            def search_filings(ticker: str, form_type: str = "10-K") -> list[Filing]:
                ...
        """

        def decorator(func: Callable[P, R]) -> Callable[P, R]:
            self._tools[name] = ToolDefinition(
                name=name,
                description=description,
                parameters=parameters,
                function=func,
            )
            logger.debug(f"Registered tool: {name}")
            return func

        return decorator

    def get_tool(self, name: str) -> ToolDefinition | None:
        """Get a tool definition by name."""
        return self._tools.get(name)

    def get_tools_for_llm(self) -> list[dict[str, Any]]:
        """
        Get all tools formatted for OpenAI's function calling API.

        Returns:
            List of tool definitions in OpenAI API format
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in self._tools.values()
        ]

    def execute(
        self,
        name: str,
        arguments: dict[str, Any],
    ) -> ToolResult:
        """
        Execute a tool by name with given arguments.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            ToolResult with execution outcome
        """
        tool = self._tools.get(name)
        if not tool:
            return ToolResult(
                tool_name=name,
                success=False,
                result=None,
                error=f"Unknown tool: {name}",
                citations=[],
                execution_time_ms=0,
            )

        if not tool.function:
            return ToolResult(
                tool_name=name,
                success=False,
                result=None,
                error=f"Tool {name} has no implementation",
                citations=[],
                execution_time_ms=0,
            )

        start_time = time.monotonic()
        try:
            result = tool.function(**arguments)
            execution_time = int((time.monotonic() - start_time) * 1000)

            # Extract citations if result contains them
            citations: list[Citation] = []
            if isinstance(result, dict) and "citations" in result:
                citations = result.pop("citations", [])

            return ToolResult(
                tool_name=name,
                success=True,
                result=result,
                error=None,
                citations=citations,
                execution_time_ms=execution_time,
            )

        except Exception as e:
            execution_time = int((time.monotonic() - start_time) * 1000)
            logger.exception(f"Tool {name} failed: {e}")
            return ToolResult(
                tool_name=name,
                success=False,
                result=None,
                error=str(e),
                citations=[],
                execution_time_ms=execution_time,
            )

    def list_tools(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())


# Global registry instance
registry = ToolRegistry()
