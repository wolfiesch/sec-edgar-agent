"""Executor agent for running tools."""

import logging
from typing import Any

from src.agents.base import (
    AgentContext,
    AgentResponse,
    AgentRole,
    BaseAgent,
    Task,
    TaskStatus,
)
from src.tools import registry

logger = logging.getLogger(__name__)

EXECUTOR_SYSTEM_PROMPT = """You are a financial research execution agent. Your job is to execute tasks by selecting and calling the appropriate tools.

## Your Responsibilities
1. Look at the current task that needs to be executed
2. Select the most appropriate tool from the available tools
3. Call the tool with the correct parameters extracted from context

## Available Tools
{tools}

## Execution Guidelines
- Use the tool_hint from the task if provided, but verify it's the right choice
- Extract parameters from the user's original query and previous results
- For company-related tools, extract the ticker symbol from the query
- If you need information from a previous task's result, use it

## Context
Original Query: {query}
Current Task: {task_description}
Tool Hint: {tool_hint}
Previous Results: {previous_results}

Select and call the appropriate tool to complete this task."""


class ExecutorAgent(BaseAgent):
    """Agent responsible for executing individual tasks using tools."""

    def __init__(self, model: str | None = None):
        super().__init__(AgentRole.EXECUTOR, model)

    def run(self, context: AgentContext) -> AgentResponse:
        """Execute the next pending task in the plan."""
        if not context.plan:
            return AgentResponse(
                success=False,
                content=None,
                error="No plan available to execute",
                should_continue=False,
            )

        # Find the next pending task
        task = self._get_next_task(context)
        if not task:
            return AgentResponse(
                success=True,
                content="All tasks completed",
                should_continue=False,
            )

        self.logger.info(f"Executing task: {task.description}")
        task.status = TaskStatus.IN_PROGRESS

        try:
            # Use Claude to determine tool and parameters
            result = self._execute_task(context, task)

            task.status = TaskStatus.COMPLETED
            task.result = result

            # Add to context
            context.tool_results.append({
                "task_id": task.id,
                "task_description": task.description,
                "result": result,
            })

            # Extract citations if present
            if isinstance(result, dict) and "citations" in result:
                context.citations.extend(result.get("citations", []))

            context.step_count += 1

            return AgentResponse(
                success=True,
                content=result,
                should_continue=self._has_more_tasks(context),
            )

        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")
            task.status = TaskStatus.FAILED
            task.error = str(e)

            return AgentResponse(
                success=False,
                content=None,
                error=str(e),
                should_continue=False,
            )

    def _get_next_task(self, context: AgentContext) -> Task | None:
        """Get the next task to execute."""
        if not context.plan:
            return None

        for task in context.plan.tasks:
            if task.status == TaskStatus.PENDING:
                # Check dependencies
                deps_met = all(
                    self._task_completed(context, dep_id)
                    for dep_id in task.dependencies
                )
                if deps_met:
                    return task

        return None

    def _task_completed(self, context: AgentContext, task_id: str) -> bool:
        """Check if a task is completed."""
        if not context.plan:
            return False

        for task in context.plan.tasks:
            if task.id == task_id:
                return task.status == TaskStatus.COMPLETED

        return False

    def _has_more_tasks(self, context: AgentContext) -> bool:
        """Check if there are more tasks to execute."""
        if not context.plan:
            return False

        return any(
            task.status == TaskStatus.PENDING
            for task in context.plan.tasks
        )

    def _execute_task(self, context: AgentContext, task: Task) -> dict[str, Any]:
        """Execute a task using Claude to select tool and parameters."""
        # Get available tools
        tools = registry.get_tools_for_llm()

        # Format previous results
        prev_results = ""
        for tr in context.tool_results[-3:]:  # Last 3 results
            prev_results += f"\n- {tr['task_description']}: {self._summarize_result(tr['result'])}"

        system_prompt = EXECUTOR_SYSTEM_PROMPT.format(
            tools=self._format_tools_detailed(tools),
            query=context.query,
            task_description=task.description,
            tool_hint=task.tool_hint or "None",
            previous_results=prev_results or "None",
        )

        messages = [
            {
                "role": "user",
                "content": f"Execute this task: {task.description}\n\nOriginal query: {context.query}",
            }
        ]

        response = self._call_llm(
            system_prompt=system_prompt,
            messages=messages,
            tools=tools,
            max_tokens=2048,
        )

        # Handle tool calls
        tool_calls = self._extract_tool_calls(response["tool_calls"])
        if tool_calls:
            # Execute the first tool call
            tool_call = tool_calls[0]
            self.logger.info(f"Calling tool: {tool_call['name']} with {tool_call['input']}")

            result = registry.execute(tool_call["name"], tool_call["input"])

            if result.success:
                return {
                    "tool": tool_call["name"],
                    "arguments": tool_call["input"],
                    "output": result.result,
                    "citations": result.citations
                }
            else:
                raise Exception(f"Tool {tool_call['name']} failed: {result.error}")

        # If no tool use, try to extract from text (fallback)
        text = self._extract_text(response["content"])
        return self._fallback_execution(context, task, text)

    def _format_tools_detailed(self, tools: list[dict[str, Any]]) -> str:
        """Format tools with full parameter details."""
        lines = []
        for tool in tools:
            func = tool.get("function", {})
            lines.append(f"\n### {func['name']}")
            lines.append(f"Description: {func['description']}")
            params = func.get("parameters", {}).get("properties", {})
            required = func.get("parameters", {}).get("required", [])

            if params:
                lines.append("Parameters:")
                for name, spec in params.items():
                    req = "(required)" if name in required else "(optional)"
                    desc = spec.get("description", "")
                    lines.append(f"  - {name} {req}: {desc}")

        return "\n".join(lines)

    def _summarize_result(self, result: Any) -> str:
        """Create a brief summary of a result."""
        # Unwrap tool execution result if present
        if isinstance(result, dict) and "tool" in result and "output" in result:
             result = result["output"]

        if isinstance(result, dict):
            if "error" in result:
                return f"Error: {result['error']}"
            if "name" in result:
                return f"Company: {result.get('name', 'Unknown')}"
            if "filings" in result:
                return f"Found {len(result['filings'])} filings"
            if "statements" in result:
                return f"Got {len(result['statements'])} financial periods"
            return str(list(result.keys()))[:100]
        return str(result)[:100]

    def _fallback_execution(
        self, context: AgentContext, task: Task, llm_text: str
    ) -> dict[str, Any]:
        """Fallback execution when Claude doesn't use tools."""
        self.logger.warning("No tool use in response, attempting fallback")

        # Try to use the tool hint
        if task.tool_hint:
            # Extract ticker from query
            ticker = self._extract_ticker(context.query)
            if ticker and task.tool_hint in registry.list_tools():
                self.logger.info(f"Fallback: calling {task.tool_hint} with ticker={ticker}")

                # Build arguments based on tool
                args: dict[str, Any] = {"ticker": ticker}

                result = registry.execute(task.tool_hint, args)
                if result.success:
                    return result.result

        return {"message": llm_text, "fallback": True}

    def _extract_ticker(self, query: str) -> str | None:
        """Extract a ticker symbol from the query."""
        import re

        # Look for common patterns
        # Uppercase 1-5 letter words that could be tickers
        words = query.upper().split()
        for word in words:
            # Clean punctuation
            clean = re.sub(r"[^A-Z]", "", word)
            if 1 <= len(clean) <= 5 and clean.isalpha():
                # Common tickers
                if clean in ["AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "TSLA", "NVDA", "JPM", "V", "JNJ", "WMT", "PG", "MA", "HD", "DIS", "NFLX", "ADBE", "CRM", "PYPL"]:
                    return clean

        # Look for "ticker" or "symbol" mentions
        match = re.search(r"(?:ticker|symbol)[:\s]+([A-Z]{1,5})", query.upper())
        if match:
            return match.group(1)

        # Take first capitalized word that looks like a ticker
        for word in words:
            clean = re.sub(r"[^A-Z]", "", word)
            if 2 <= len(clean) <= 5:
                return clean

        return None
