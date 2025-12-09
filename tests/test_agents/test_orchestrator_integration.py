"""Integration tests for agent orchestration."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from src.agents.base import AgentContext, Plan, Task, TaskStatus
from src.agents.orchestrator import Orchestrator


def create_text_block(text: str) -> Mock:
    """Create a mock Anthropic text content block."""
    block = Mock()
    block.type = "text"
    block.text = text
    return block


def create_tool_use_block(tool_id: str, name: str, input_data: dict) -> Mock:
    """Create a mock Anthropic tool use content block."""
    block = Mock()
    block.type = "tool_use"
    block.id = tool_id
    block.name = name
    block.input = input_data
    return block


class TestOrchestratorIntegration:
    """Integration tests for the full agent workflow."""

    @patch("src.agents.base.BaseAgent._call_claude")
    def test_simple_query_workflow(self, mock_call_claude: MagicMock) -> None:
        """Test orchestrator with a simple query."""
        # Mock planner response
        plan_json = """{
            "reasoning": "Simple company info lookup",
            "is_simple": true,
            "tasks": [
                {
                    "id": "task_1",
                    "description": "Get Apple company information",
                    "tool_hint": "get_company_info",
                    "dependencies": []
                }
            ]
        }"""

        # Mock executor response (tool result)
        tool_result = """{
            "success": true,
            "ticker": "AAPL",
            "name": "Apple Inc.",
            "cik": "0000320193"
        }"""

        # Mock synthesizer response
        synthesis = "Apple Inc. (AAPL) is a technology company with CIK 0000320193."

        mock_call_claude.side_effect = [
            {"content": [create_text_block(plan_json)]},  # Planner
            {  # Executor with tool use
                "content": [create_tool_use_block("toolu_1", "get_company_info", {"ticker": "AAPL"})]
            },
            {"content": [create_text_block(synthesis)]},  # Synthesizer
        ]

        orchestrator = Orchestrator()

        # Mock tool execution
        with patch("src.agents.executor.registry.execute") as mock_execute:
            from src.data.models import ToolResult

            mock_execute.return_value = ToolResult(
                tool_name="get_company_info",
                success=True,
                result={"ticker": "AAPL", "name": "Apple Inc.", "cik": "0000320193"},
                execution_time_ms=100,
            )

            result = orchestrator.run("What is Apple's ticker symbol?")

            assert isinstance(result, str)
            assert len(result) > 0
            # Planner, Executor, Synthesizer should be called (no validation for simple)
            assert mock_call_claude.call_count == 3

    @patch("src.agents.base.BaseAgent._call_claude")
    def test_complex_query_workflow(self, mock_call_claude: MagicMock) -> None:
        """Test orchestrator with a complex multi-step query."""
        # Mock planner response - multi-step plan
        plan_json = """{
            "reasoning": "Need to fetch financials and calculate growth",
            "is_simple": false,
            "tasks": [
                {
                    "id": "task_1",
                    "description": "Get Apple income statements for 3 years",
                    "tool_hint": "get_income_statement",
                    "dependencies": []
                },
                {
                    "id": "task_2",
                    "description": "Calculate revenue growth rate",
                    "tool_hint": "analyze_historical_trends",
                    "dependencies": ["task_1"]
                }
            ]
        }"""

        # Mock responses for each phase
        mock_call_claude.side_effect = [
            {"content": [create_text_block(plan_json)]},  # Planner
            {  # Executor - task 1
                "content": [
                    create_tool_use_block(
                        "toolu_1", "get_income_statement", {"ticker": "AAPL", "periods": 3}
                    )
                ]
            },
            {  # Executor - task 2
                "content": [
                    create_tool_use_block(
                        "toolu_2", "analyze_historical_trends", {"ticker": "AAPL", "metric": "revenue"}
                    )
                ]
            },
            {"content": [create_text_block('{"valid": true, "confidence": 0.95}')]},  # Validator
            {  # Synthesizer
                "content": [create_text_block("Apple's revenue has grown at 12% CAGR over 3 years.")]
            },
        ]

        orchestrator = Orchestrator()

        with patch("src.agents.executor.registry.execute") as mock_execute:
            from src.data.models import ToolResult

            # Mock tool executions
            mock_execute.side_effect = [
                ToolResult(
                    tool_name="get_income_statement",
                    success=True,
                    result={
                        "ticker": "AAPL",
                        "periods": 3,
                        "statements": [
                            {"fiscal_year": 2024, "data": {"Revenue": 100000000000}},
                            {"fiscal_year": 2023, "data": {"Revenue": 90000000000}},
                            {"fiscal_year": 2022, "data": {"Revenue": 80000000000}},
                        ],
                    },
                    execution_time_ms=500,
                ),
                ToolResult(
                    tool_name="analyze_historical_trends",
                    success=True,
                    result={"ticker": "AAPL", "cagr": 0.12, "trend": "increasing"},
                    execution_time_ms=200,
                ),
            ]

            result = orchestrator.run("What is Apple's revenue growth over 3 years?")

            assert isinstance(result, str)
            # Should call planner, executor (2x), validator, synthesizer
            assert mock_call_claude.call_count == 5
            assert mock_execute.call_count == 2

    @patch("src.agents.base.BaseAgent._call_claude")
    def test_workflow_with_tool_failure(self, mock_call_claude: MagicMock) -> None:
        """Test that workflow handles tool failures gracefully."""
        plan_json = """{
            "reasoning": "Lookup company info",
            "is_simple": true,
            "tasks": [
                {
                    "id": "task_1",
                    "description": "Get company info",
                    "tool_hint": "get_company_info",
                    "dependencies": []
                }
            ]
        }"""

        mock_call_claude.side_effect = [
            {"content": [create_text_block(plan_json)]},  # Planner
            {  # Executor
                "content": [
                    create_tool_use_block("toolu_1", "get_company_info", {"ticker": "INVALID"})
                ]
            },
            {  # Synthesizer (should still run)
                "content": [create_text_block("Unable to find company information for INVALID.")]
            },
        ]

        orchestrator = Orchestrator()

        with patch("src.agents.executor.registry.execute") as mock_execute:
            from src.data.models import ToolResult

            # Mock tool failure
            mock_execute.return_value = ToolResult(
                tool_name="get_company_info",
                success=False,
                result=None,
                error="Company not found",
                execution_time_ms=50,
            )

            result = orchestrator.run("Get info for ticker INVALID")

            assert isinstance(result, str)
            # Should still complete workflow
            assert mock_call_claude.call_count >= 2

    @patch("src.agents.base.BaseAgent._call_claude")
    def test_max_steps_limit(self, mock_call_claude: MagicMock) -> None:
        """Test that orchestrator respects max_steps limit."""
        # Create a plan with many tasks
        plan_json = """{
            "reasoning": "Complex analysis",
            "is_simple": false,
            "tasks": [%s]
        }""" % ",".join(
            [
                f'{{"id": "task_{i}", "description": "Task {i}", '
                f'"tool_hint": "get_company_info", "dependencies": []}}'
                for i in range(25)  # More than max_steps
            ]
        )

        mock_call_claude.side_effect = [
            {"content": [create_text_block(plan_json)]},  # Planner
        ] + [
            {  # Executor responses
                "content": [
                    create_tool_use_block(f"toolu_{i}", "get_company_info", {"ticker": "AAPL"})
                ]
            }
            for i in range(25)
        ] + [
            {"content": [create_text_block("{}")]},  # Validator
            {"content": [create_text_block("Result")]},  # Synthesizer
        ]

        orchestrator = Orchestrator()
        orchestrator.max_steps = 5  # Set low limit

        with patch("src.agents.executor.registry.execute") as mock_execute:
            from src.data.models import ToolResult

            mock_execute.return_value = ToolResult(
                tool_name="get_company_info",
                success=True,
                result={"ticker": "AAPL"},
                execution_time_ms=100,
            )

            result = orchestrator.run("Complex query")

            # Should stop at max_steps, not execute all 25 tasks
            assert mock_execute.call_count <= orchestrator.max_steps


class TestOrchestratorErrorHandling:
    """Test error handling in orchestrator."""

    @patch("src.agents.planner.PlannerAgent.run")
    def test_planner_failure(self, mock_planner: MagicMock) -> None:
        """Test handling when planner fails."""
        from src.agents.base import AgentResponse

        mock_planner.return_value = AgentResponse(
            success=False, content=None, error="Failed to parse query"
        )

        orchestrator = Orchestrator()
        result = orchestrator.run("Invalid query ???")

        assert isinstance(result, str)
        assert "Failed to create plan" in result

    @patch("src.agents.base.BaseAgent._call_claude")
    def test_executor_continuous_failure(self, mock_call_claude: MagicMock) -> None:
        """Test that executor failures don't block completion."""
        plan_json = """{
            "reasoning": "Test plan",
            "is_simple": true,
            "tasks": [
                {"id": "task_1", "description": "Task 1", "tool_hint": null, "dependencies": []},
                {"id": "task_2", "description": "Task 2", "tool_hint": null, "dependencies": []}
            ]
        }"""

        mock_call_claude.side_effect = [
            {"content": [create_text_block(plan_json)]},
            {"content": [create_text_block("Executor response")]},
            {"content": [create_text_block("Executor response")]},
            {"content": [create_text_block("Final response")]},
        ]

        orchestrator = Orchestrator()

        with patch("src.agents.executor.ExecutorAgent.run") as mock_executor:
            from src.agents.base import AgentResponse

            # Executor always fails but returns should_continue=False after attempts
            mock_executor.side_effect = [
                AgentResponse(success=False, content=None, error="Failed", should_continue=True),
                AgentResponse(success=False, content=None, error="Failed", should_continue=False),
            ]

            result = orchestrator.run("Test query")

            assert isinstance(result, str)
            # Should reach synthesizer despite failures
            assert mock_call_claude.call_count >= 1
