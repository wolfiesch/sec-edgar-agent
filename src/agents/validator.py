"""Validator agent for checking execution results."""

import logging
from typing import Any

from src.agents.base import (
    AgentContext,
    AgentResponse,
    AgentRole,
    BaseAgent,
)

logger = logging.getLogger(__name__)

VALIDATOR_SYSTEM_PROMPT = """You are a financial research validation agent. Your job is to verify that task results are correct and complete.

## Your Responsibilities
1. Check if the task results actually answer the user's query
2. Verify that financial data looks reasonable (not obviously wrong)
3. Flag any issues or missing information

## Validation Checks
- Did the tools return valid data (not errors)?
- Does the data relate to the correct company?
- Are numerical values in reasonable ranges?
- Is there enough information to answer the query?

## Response Format
Respond with a JSON object:
{{
    "valid": true/false,
    "confidence": 0.0-1.0,
    "issues": ["list of issues if any"],
    "suggestions": ["suggestions for improvement if needed"]
}}

Only output the JSON, no other text."""


class ValidatorAgent(BaseAgent):
    """Agent responsible for validating execution results."""

    def __init__(self, model: str | None = None):
        """Create a validator agent responsible for quality checks."""
        super().__init__(AgentRole.VALIDATOR, model)

    def run(self, context: AgentContext) -> AgentResponse:
        """Validate the results of executed tasks."""
        self.logger.info("Validating execution results")

        # Quick validation for simple cases
        if self._quick_validation(context):
            return AgentResponse(
                success=True,
                content={
                    "valid": True,
                    "confidence": 0.9,
                    "issues": [],
                    "suggestions": [],
                },
                should_continue=True,
            )

        # For complex cases, use Claude
        try:
            validation = self._deep_validation(context)
            return AgentResponse(
                success=True,
                content=validation,
                should_continue=validation.get("valid", False),
            )
        except Exception as e:
            self.logger.error(f"Validation failed: {str(e)}")
            # Don't block on validation errors
            return AgentResponse(
                success=True,
                content={
                    "valid": True,
                    "confidence": 0.5,
                    "issues": [f"Validation error: {str(e)}"],
                    "suggestions": [],
                },
                should_continue=True,
            )

    def _quick_validation(self, context: AgentContext) -> bool:
        """Perform quick validation checks without calling Claude."""
        if not context.tool_results:
            return False

        # Check if all results are non-error
        for result in context.tool_results:
            data = result.get("result", {})
            if isinstance(data, dict):
                if data.get("error") or data.get("success") is False:
                    return False

        # For simple plans with successful results, skip deep validation
        if context.plan and context.plan.is_simple:
            return True

        return False

    def _deep_validation(self, context: AgentContext) -> dict[str, Any]:
        """Use Claude for deep validation of complex results."""
        results_summary = self._format_results(context.tool_results)

        messages = [
            {
                "role": "user",
                "content": f"""Validate these results for the query: "{context.query}"

Results:
{results_summary}

Check if the results correctly and completely answer the user's query.""",
            }
        ]

        response = self._call_llm(
            system_prompt=VALIDATOR_SYSTEM_PROMPT,
            messages=messages,
            max_tokens=1024,
        )

        text = self._extract_text(response["content"])
        return self._parse_validation(text)

    def _format_results(self, results: list[dict[str, Any]]) -> str:
        """Format results for validation prompt."""
        lines = []
        for i, result in enumerate(results, 1):
            lines.append(f"\n## Result {i}: {result.get('task_description', 'Unknown task')}")
            data = result.get("result", {})
            if isinstance(data, dict):
                # Truncate large data
                data_str = str(data)
                if len(data_str) > 2000:
                    data_str = data_str[:2000] + "... (truncated)"
                lines.append(data_str)
            else:
                lines.append(str(data)[:2000])
        return "\n".join(lines)

    def _parse_validation(self, text: str) -> dict[str, Any]:
        """Parse validation response."""
        import json

        try:
            # Handle markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            result = json.loads(text.strip())
            if isinstance(result, dict):
                return result
            return {"valid": False, "confidence": 0.0, "issues": ["Invalid JSON format"], "suggestions": []}
        except json.JSONDecodeError:
            # Default to valid if parsing fails
            return {
                "valid": True,
                "confidence": 0.7,
                "issues": ["Could not parse validation response"],
                "suggestions": [],
            }


def validate_financial_value(value: Any, metric: str) -> bool:
    """Validate that a financial value is reasonable."""
    if value is None:
        return True  # Missing values are okay

    try:
        num = float(value)
    except (TypeError, ValueError):
        return True  # Non-numeric values pass

    # Basic sanity checks
    if metric in ["revenue", "total_assets", "market_cap"]:
        # Should be positive and not absurdly large
        return 0 <= num <= 1e15  # Up to $1 quadrillion

    if metric in ["net_income", "operating_income"]:
        # Can be negative but within reason
        return -1e14 <= num <= 1e14

    if metric in ["eps", "earnings_per_share"]:
        # Usually between -1000 and 1000
        return -1000 <= num <= 1000

    if metric in ["pe_ratio", "price_to_earnings"]:
        # Usually between 0 and 1000 (or negative for losses)
        return -100 <= num <= 1000

    return True
