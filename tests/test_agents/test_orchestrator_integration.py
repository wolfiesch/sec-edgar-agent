"""Integration tests for agent orchestration."""

import json
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.agents.base import AgentContext, Plan, Task, TaskStatus
from src.agents.orchestrator import Orchestrator


def create_openai_response(content: str, tool_calls: list | None = None) -> Mock:
    """Create a mock OpenAI ChatCompletion response."""
    response = Mock()
    response.choices = [Mock()]
    response.choices[0].message = Mock()
    response.choices[0].message.content = content
    response.choices[0].message.tool_calls = tool_calls
    response.choices[0].finish_reason = "stop"
    response.usage = Mock()
    response.usage.prompt_tokens = 100
    response.usage.completion_tokens = 50
    return response


def create_tool_call(tool_id: str, name: str, input_data: dict) -> Mock:
    """Create a mock OpenAI tool call."""
    tool_call = Mock()
    tool_call.id = tool_id
    tool_call.type = "function"
    tool_call.function = Mock()
    tool_call.function.name = name
    tool_call.function.arguments = json.dumps(input_data)
    return tool_call


class TestOrchestratorIntegration:
    """Integration tests for the full agent workflow."""

    @patch("src.agents.base.BaseAgent._call_llm")
    def test_simple_query_workflow(self, mock_call_llm: MagicMock) -> None:
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

        # Mock synthesizer response
        synthesis = "Apple Inc. (AAPL) is a technology company with CIK 0000320193."

        mock_call_llm.side_effect = [
            {  # Planner
                "content": plan_json,
                "tool_calls": None,
                "finish_reason": "stop",
                "usage": {"input_tokens": 100, "output_tokens": 50},
            },
            {  # Executor with tool call
                "content": None,
                "tool_calls": [create_tool_call("call_1", "get_company_info", {"ticker": "AAPL"})],
                "finish_reason": "tool_calls",
                "usage": {"input_tokens": 100, "output_tokens": 50},
            },
            {  # Synthesizer
                "content": synthesis,
                "tool_calls": None,
                "finish_reason": "stop",
                "usage": {"input_tokens": 100, "output_tokens": 50},
            },
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
            assert mock_call_llm.call_count == 3

    @patch("src.agents.base.BaseAgent._call_llm")
    def test_complex_query_workflow(self, mock_call_llm: MagicMock) -> None:
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
        mock_call_llm.side_effect = [
            {"content": plan_json, "tool_calls": None, "finish_reason": "stop", "usage": {"input_tokens": 100, "output_tokens": 50}},  # Planner
            {"content": None, "tool_calls": [create_tool_call(
                        "toolu_1", "get_income_statement", {"ticker": "AAPL", "periods": 3}
                    )], "finish_reason": "tool_calls", "usage": {"input_tokens": 100, "output_tokens": 50}},
            {"content": None, "tool_calls": [create_tool_call(
                        "toolu_2", "analyze_historical_trends", {"ticker": "AAPL", "metric": "revenue"}
                    )], "finish_reason": "tool_calls", "usage": {"input_tokens": 100, "output_tokens": 50}},
            {"content": '{"valid": true, "confidence": 0.95}', "tool_calls": None, "finish_reason": "stop", "usage": {"input_tokens": 100, "output_tokens": 50}},  # Validator
            {  # Synthesizer
                "content": "Apple's revenue has grown at 12% CAGR over 3 years.", "tool_calls": None, "finish_reason": "stop", "usage": {"input_tokens": 100, "output_tokens": 50}
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
            assert mock_call_llm.call_count == 5
            assert mock_execute.call_count == 2

    @patch("src.agents.base.BaseAgent._call_llm")
    def test_workflow_with_tool_failure(self, mock_call_llm: MagicMock) -> None:
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

        mock_call_llm.side_effect = [
            {"content": plan_json, "tool_calls": None, "finish_reason": "stop", "usage": {"input_tokens": 100, "output_tokens": 50}},  # Planner
            {"content": None, "tool_calls": [create_tool_call("toolu_1", "get_company_info", {"ticker": "INVALID"})], "finish_reason": "tool_calls", "usage": {"input_tokens": 100, "output_tokens": 50}},
            {  # Synthesizer (should still run)
                "content": "Unable to find company information for INVALID.", "tool_calls": None, "finish_reason": "stop", "usage": {"input_tokens": 100, "output_tokens": 50}
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
            assert mock_call_llm.call_count >= 2

    @patch("src.agents.base.BaseAgent._call_llm")
    def test_max_steps_limit(self, mock_call_llm: MagicMock) -> None:
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

        mock_call_llm.side_effect = [
            {"content": plan_json, "tool_calls": None, "finish_reason": "stop", "usage": {"input_tokens": 100, "output_tokens": 50}},  # Planner
        ] + [
            {"content": None, "tool_calls": [create_tool_call(f"toolu_{i}", "get_company_info", {"ticker": "AAPL"})], "finish_reason": "tool_calls", "usage": {"input_tokens": 100, "output_tokens": 50}}
            for i in range(25)
        ] + [
            {"content": "{}", "tool_calls": None, "finish_reason": "stop", "usage": {"input_tokens": 100, "output_tokens": 50}},  # Validator
            {"content": "Result", "tool_calls": None, "finish_reason": "stop", "usage": {"input_tokens": 100, "output_tokens": 50}},  # Synthesizer
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

    @patch("src.agents.base.BaseAgent._call_llm")
    def test_executor_continuous_failure(self, mock_call_llm: MagicMock) -> None:
        """Test that executor failures don't block completion."""
        plan_json = """{
            "reasoning": "Test plan",
            "is_simple": true,
            "tasks": [
                {"id": "task_1", "description": "Task 1", "tool_hint": null, "dependencies": []},
                {"id": "task_2", "description": "Task 2", "tool_hint": null, "dependencies": []}
            ]
        }"""

        mock_call_llm.side_effect = [
            {"content": plan_json, "tool_calls": None, "finish_reason": "stop", "usage": {"input_tokens": 100, "output_tokens": 50}},
            {"content": "Executor response", "tool_calls": None, "finish_reason": "stop", "usage": {"input_tokens": 100, "output_tokens": 50}},
            {"content": "Executor response", "tool_calls": None, "finish_reason": "stop", "usage": {"input_tokens": 100, "output_tokens": 50}},
            {"content": "Final response", "tool_calls": None, "finish_reason": "stop", "usage": {"input_tokens": 100, "output_tokens": 50}},
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
            assert mock_call_llm.call_count >= 1
