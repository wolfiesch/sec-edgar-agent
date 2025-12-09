"""Planner agent for task decomposition."""

import json
import logging
import uuid
from typing import Any

from src.agents.base import (
    AgentContext,
    AgentResponse,
    AgentRole,
    BaseAgent,
    Plan,
    Task,
    TaskStatus,
)
from src.tools import registry

logger = logging.getLogger(__name__)

PLANNER_SYSTEM_PROMPT = """You are a financial research planning agent. Your job is to analyze user queries about SEC filings and companies, then create an execution plan.

## Your Responsibilities
1. Understand what the user is asking about (company info, filings, financials, etc.)
2. Determine which tools are needed to answer the query
3. Create a structured plan with specific tasks

## Available Tools
{tools}

## Planning Guidelines
- For simple queries (single company lookup, basic info), create a simple plan with 1-2 tasks
- For complex queries (comparisons, multi-step analysis), break down into logical steps
- Always consider dependencies - some tasks may need results from earlier tasks
- If a query is ambiguous, plan to gather more information first

## Response Format
You must respond with a valid JSON object:
{{
    "reasoning": "Brief explanation of your planning approach",
    "is_simple": true/false,
    "tasks": [
        {{
            "id": "task_1",
            "description": "What this task does",
            "tool_hint": "suggested_tool_name or null",
            "dependencies": []
        }}
    ]
}}

Only output the JSON, no other text."""


class PlannerAgent(BaseAgent):
    """Agent responsible for breaking down queries into executable tasks."""

    def __init__(self, model: str | None = None):
        super().__init__(AgentRole.PLANNER, model)

    def run(self, context: AgentContext) -> AgentResponse:
        """Create a plan for the user's query."""
        self.logger.info(f"Planning query: {context.query}")

        # Get available tools for the prompt
        tools = registry.get_tools_for_llm()
        tools_description = self._format_tools(tools)

        system_prompt = PLANNER_SYSTEM_PROMPT.format(tools=tools_description)

        messages = [
            {
                "role": "user",
                "content": f"Create a plan to answer this query: {context.query}",
            }
        ]

        try:
            response = self._call_llm(
                system_prompt=system_prompt,
                messages=messages,
                max_tokens=2048,
            )

            text = self._extract_text(response["content"])
            plan_data = self._parse_plan(text, context.query)

            context.plan = plan_data

            self.logger.info(
                f"Created plan with {len(plan_data.tasks)} tasks "
                f"(simple={plan_data.is_simple})"
            )

            return AgentResponse(
                success=True,
                content=plan_data,
                should_continue=True,
            )

        except Exception as e:
            self.logger.error(f"Planning failed: {e}")
            # Create a fallback simple plan
            fallback_plan = self._create_fallback_plan(context.query)
            context.plan = fallback_plan

            return AgentResponse(
                success=True,
                content=fallback_plan,
                error=f"Used fallback plan due to: {str(e)}",
                should_continue=True,
            )

    def _format_tools(self, tools: list[dict[str, Any]]) -> str:
        """Format tools for the system prompt."""
        lines = []
        for tool in tools:
            func = tool.get("function", {})
            params = func.get("parameters", {}).get("properties", {})
            param_names = list(params.keys())
            lines.append(f"- {func['name']}: {func['description']}")
            if param_names:
                lines.append(f"  Parameters: {', '.join(param_names)}")
        return "\n".join(lines)

    def _parse_plan(self, text: str, query: str) -> Plan:
        """Parse the LLM response into a Plan object."""
        # Try to extract JSON from the response
        try:
            # Handle potential markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            data = json.loads(text.strip())

            tasks = []
            for task_data in data.get("tasks", []):
                task = Task(
                    id=task_data.get("id", f"task_{uuid.uuid4().hex[:8]}"),
                    description=task_data.get("description", ""),
                    tool_hint=task_data.get("tool_hint"),
                    status=TaskStatus.PENDING,
                    dependencies=task_data.get("dependencies", []),
                )
                tasks.append(task)

            return Plan(
                query=query,
                reasoning=data.get("reasoning", ""),
                tasks=tasks,
                is_simple=data.get("is_simple", len(tasks) <= 2),
            )

        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse plan JSON: {e}")
            raise

    def _create_fallback_plan(self, query: str) -> Plan:
        """Create a simple fallback plan when parsing fails."""
        # Try to detect intent from query
        query_lower = query.lower()

        if any(word in query_lower for word in ["company", "info", "about"]):
            tool_hint = "get_company_info"
            desc = "Get company information"
        elif any(word in query_lower for word in ["filing", "10-k", "10-q", "8-k"]):
            tool_hint = "search_filings"
            desc = "Search for relevant filings"
        elif any(word in query_lower for word in ["revenue", "income", "profit", "earnings"]):
            tool_hint = "get_income_statement"
            desc = "Get income statement data"
        elif any(word in query_lower for word in ["balance", "assets", "debt", "equity"]):
            tool_hint = "get_balance_sheet"
            desc = "Get balance sheet data"
        elif any(word in query_lower for word in ["cash flow", "cash"]):
            tool_hint = "get_cash_flow"
            desc = "Get cash flow statement"
        elif any(word in query_lower for word in ["insider", "buy", "sell", "trading"]):
            tool_hint = "get_insider_trades"
            desc = "Get insider trading activity"
        else:
            tool_hint = "search_filings"
            desc = "Search for relevant information"

        return Plan(
            query=query,
            reasoning="Fallback plan created due to parsing error",
            tasks=[
                Task(
                    id="task_1",
                    description=desc,
                    tool_hint=tool_hint,
                    status=TaskStatus.PENDING,
                )
            ],
            is_simple=True,
        )
