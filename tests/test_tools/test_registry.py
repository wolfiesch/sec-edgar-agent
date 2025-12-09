"""Tests for tool registry."""

import pytest

from src.data.models import Citation
from src.tools.registry import ToolDefinition, ToolRegistry


class TestToolRegistry:
    """Tests for ToolRegistry class."""

    @pytest.fixture
    def registry(self) -> ToolRegistry:
        """Create a fresh registry."""
        return ToolRegistry()

    def test_init_empty(self, registry: ToolRegistry) -> None:
        """Test that registry starts empty."""
        assert registry.list_tools() == []

    def test_register_tool(self, registry: ToolRegistry) -> None:
        """Test registering a tool."""

        @registry.register(
            name="test_tool",
            description="A test tool",
            parameters={
                "type": "object",
                "properties": {"arg": {"type": "string"}},
                "required": ["arg"],
            },
        )
        def test_func(arg: str) -> str:
            return f"Result: {arg}"

        assert "test_tool" in registry.list_tools()
        tool = registry.get_tool("test_tool")
        assert tool is not None
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"

    def test_register_multiple_tools(self, registry: ToolRegistry) -> None:
        """Test registering multiple tools."""

        @registry.register(
            name="tool1",
            description="First tool",
            parameters={"type": "object", "properties": {}},
        )
        def func1() -> str:
            return "one"

        @registry.register(
            name="tool2",
            description="Second tool",
            parameters={"type": "object", "properties": {}},
        )
        def func2() -> str:
            return "two"

        tools = registry.list_tools()
        assert len(tools) == 2
        assert "tool1" in tools
        assert "tool2" in tools

    def test_get_nonexistent_tool(self, registry: ToolRegistry) -> None:
        """Test getting a nonexistent tool returns None."""
        tool = registry.get_tool("nonexistent")
        assert tool is None

    def test_get_tools_for_llm_empty(self, registry: ToolRegistry) -> None:
        """Test getting tools for LLM when empty."""
        tools = registry.get_tools_for_llm()
        assert tools == []

    def test_get_tools_for_llm_format(self, registry: ToolRegistry) -> None:
        """Test tools are formatted correctly for Claude API."""

        @registry.register(
            name="search",
            description="Search for something",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"],
            },
        )
        def search(query: str) -> dict[str, str]:
            return {"result": query}

        tools = registry.get_tools_for_llm()
        assert len(tools) == 1

        tool = tools[0]
        assert tool["name"] == "search"
        assert tool["description"] == "Search for something"
        assert "input_schema" in tool
        assert tool["input_schema"]["type"] == "object"
        assert "query" in tool["input_schema"]["properties"]

    def test_execute_tool_success(self, registry: ToolRegistry) -> None:
        """Test executing a tool successfully."""

        @registry.register(
            name="add",
            description="Add two numbers",
            parameters={
                "type": "object",
                "properties": {
                    "a": {"type": "number"},
                    "b": {"type": "number"},
                },
                "required": ["a", "b"],
            },
        )
        def add(a: int, b: int) -> dict[str, int]:
            return {"sum": a + b}

        result = registry.execute("add", {"a": 5, "b": 3})

        assert result.success is True
        assert result.tool_name == "add"
        assert result.result == {"sum": 8}
        assert result.error is None
        assert result.execution_time_ms >= 0

    def test_execute_tool_with_citations(self, registry: ToolRegistry) -> None:
        """Test that citations are extracted from results."""
        from datetime import date

        @registry.register(
            name="get_data",
            description="Get data",
            parameters={"type": "object", "properties": {}},
        )
        def get_data() -> dict[str, list[Citation] | str]:
            return {
                "data": "some data",
                "citations": [
                    Citation(
                        ticker="AAPL",
                        form_type="10-K",
                        filing_date=date(2024, 10, 31),
                        accession_number="0000320193-24-000123",
                    )
                ],
            }

        result = registry.execute("get_data", {})

        assert result.success is True
        assert len(result.citations) == 1
        assert result.citations[0].ticker == "AAPL"
        # Citations should be removed from result
        assert "citations" not in result.result

    def test_execute_nonexistent_tool(self, registry: ToolRegistry) -> None:
        """Test executing a nonexistent tool."""
        result = registry.execute("nonexistent", {})

        assert result.success is False
        assert result.tool_name == "nonexistent"
        assert result.error == "Unknown tool: nonexistent"
        assert result.execution_time_ms == 0

    def test_execute_tool_with_exception(self, registry: ToolRegistry) -> None:
        """Test executing a tool that raises an exception."""

        @registry.register(
            name="failing_tool",
            description="A tool that fails",
            parameters={"type": "object", "properties": {}},
        )
        def failing_tool() -> None:
            raise ValueError("Something went wrong")

        result = registry.execute("failing_tool", {})

        assert result.success is False
        assert result.tool_name == "failing_tool"
        assert "Something went wrong" in result.error
        assert result.execution_time_ms >= 0

    def test_execute_tool_with_wrong_arguments(self, registry: ToolRegistry) -> None:
        """Test executing a tool with wrong arguments."""

        @registry.register(
            name="needs_arg",
            description="Needs an argument",
            parameters={
                "type": "object",
                "properties": {"required_arg": {"type": "string"}},
                "required": ["required_arg"],
            },
        )
        def needs_arg(required_arg: str) -> str:
            return required_arg

        # Missing required argument
        result = registry.execute("needs_arg", {})

        assert result.success is False
        assert result.execution_time_ms >= 0


class TestToolDefinition:
    """Tests for ToolDefinition model."""

    def test_tool_definition_creation(self) -> None:
        """Test creating a ToolDefinition."""

        def sample_func() -> str:
            return "test"

        tool = ToolDefinition(
            name="test",
            description="A test tool",
            parameters={"type": "object"},
            function=sample_func,
        )

        assert tool.name == "test"
        assert tool.description == "A test tool"
        assert tool.parameters == {"type": "object"}
        assert tool.function is sample_func

    def test_tool_definition_without_function(self) -> None:
        """Test creating a ToolDefinition without a function."""
        tool = ToolDefinition(
            name="test",
            description="A test tool",
            parameters={"type": "object"},
        )

        assert tool.function is None


class TestRegistryIntegration:
    """Integration tests for registry with real tool patterns."""

    @pytest.fixture
    def registry(self) -> ToolRegistry:
        """Create a fresh registry."""
        return ToolRegistry()

    def test_typical_search_tool_pattern(self, registry: ToolRegistry) -> None:
        """Test a typical search tool registration and execution."""

        @registry.register(
            name="search_filings",
            description="Search for SEC filings",
            parameters={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker"},
                    "form_type": {
                        "type": "string",
                        "description": "Form type (10-K, 10-Q)",
                    },
                    "limit": {"type": "integer", "description": "Max results"},
                },
                "required": ["ticker"],
            },
        )
        def search_filings(
            ticker: str, form_type: str = "10-K", limit: int = 10
        ) -> dict[str, str | int]:
            return {
                "ticker": ticker,
                "form_type": form_type,
                "count": limit,
            }

        # Verify registration
        tool = registry.get_tool("search_filings")
        assert tool is not None

        # Verify LLM format
        llm_tools = registry.get_tools_for_llm()
        assert len(llm_tools) == 1
        assert llm_tools[0]["name"] == "search_filings"

        # Execute with required arg only
        result = registry.execute("search_filings", {"ticker": "AAPL"})
        assert result.success is True
        assert result.result["ticker"] == "AAPL"
        assert result.result["form_type"] == "10-K"

        # Execute with all args
        result = registry.execute(
            "search_filings", {"ticker": "MSFT", "form_type": "10-Q", "limit": 5}
        )
        assert result.success is True
        assert result.result["ticker"] == "MSFT"
        assert result.result["form_type"] == "10-Q"
        assert result.result["count"] == 5
