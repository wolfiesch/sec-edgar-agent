"""Synthesizer agent for generating final responses."""

import logging
from typing import Any

from src.agents.base import (
    AgentContext,
    AgentResponse,
    AgentRole,
    BaseAgent,
)
from src.utils.citations import format_citations

logger = logging.getLogger(__name__)

SYNTHESIZER_SYSTEM_PROMPT = """You are a financial research synthesis agent. Your job is to take research results and create a clear, accurate response for the user.

## Your Responsibilities
1. Synthesize all research results into a coherent answer
2. Present financial data clearly with proper formatting
3. Include citations for all factual claims
4. Highlight key insights and important findings

## Response Guidelines
- Start with a direct answer to the user's question
- Use bullet points and tables for financial data
- Include specific numbers with proper units (millions, billions)
- Always cite your sources using the format: [TICKER FORM YEAR]
- If data is incomplete or uncertain, say so
- Keep responses concise but comprehensive

## Citation Format
When citing SEC filings, use: [TICKER FORM YEAR]
Example: [AAPL 10-K 2024] or [MSFT 10-Q 2024, Q3]

## User Query
{query}

## Research Results
{results}

## Available Citations
{citations}

Now synthesize a response that directly answers the user's query."""


class SynthesizerAgent(BaseAgent):
    """Agent responsible for synthesizing final responses."""

    def __init__(self, model: str | None = None):
        super().__init__(AgentRole.SYNTHESIZER, model)

    def run(self, context: AgentContext) -> AgentResponse:
        """Synthesize research results into a final response."""
        self.logger.info("Synthesizing response")

        if not context.tool_results:
            return AgentResponse(
                success=False,
                content=None,
                error="No results to synthesize",
                should_continue=False,
            )

        try:
            response = self._generate_response(context)
            return AgentResponse(
                success=True,
                content=response,
                should_continue=False,
            )
        except Exception as e:
            self.logger.error(f"Synthesis failed: {e}")
            # Generate a basic response from raw results
            fallback = self._fallback_response(context)
            return AgentResponse(
                success=True,
                content=fallback,
                error=f"Used fallback synthesis: {str(e)}",
                should_continue=False,
            )

    def _generate_response(self, context: AgentContext) -> str:
        """Generate a synthesized response using Claude."""
        results_text = self._format_results(context.tool_results)
        citations_text = format_citations(context.citations) if context.citations else "No specific citations available"

        system_prompt = SYNTHESIZER_SYSTEM_PROMPT.format(
            query=context.query,
            results=results_text,
            citations=citations_text,
        )

        messages = [
            {
                "role": "user",
                "content": "Please synthesize the research results and provide a clear answer to my query.",
            }
        ]

        response = self._call_llm(
            system_prompt=system_prompt,
            messages=messages,
            max_tokens=4096,
        )

        text = self._extract_text(response["content"])

        # Append citations if not already included
        if context.citations and "[" not in text:
            text += f"\n\n**Sources:** {citations_text}"

        return text

    def _format_results(self, results: list[dict[str, Any]]) -> str:
        """Format results for the synthesis prompt."""
        lines = []

        for result in results:
            task_desc = result.get("task_description", "Unknown task")
            data = result.get("result", {})

            lines.append(f"\n### {task_desc}")

            if isinstance(data, dict):
                if data.get("success") is False:
                    lines.append(f"Error: {data.get('error', 'Unknown error')}")
                    continue

                # Format based on data type
                if "filings" in data:
                    lines.append(f"Found {data.get('count', len(data['filings']))} filings:")
                    for f in data["filings"][:5]:
                        lines.append(f"  - {f.get('form_type', 'Unknown')} filed {f.get('filing_date', 'Unknown')}")

                elif "statements" in data:
                    lines.append(f"Financial data for {data.get('ticker', 'Unknown')}:")
                    for stmt in data["statements"][:3]:
                        lines.append(f"  FY{stmt.get('fiscal_year', '?')}:")
                        stmt_data = stmt.get("data", {})
                        for key, value in list(stmt_data.items())[:10]:
                            lines.append(f"    - {key}: {self._format_value(value)}")

                elif "by_insider" in data:
                    lines.append(f"Insider trading for {data.get('ticker', 'Unknown')}:")
                    for insider in data["by_insider"][:5]:
                        bought = insider.get("total_bought", 0)
                        sold = insider.get("total_sold", 0)
                        lines.append(f"  - {insider.get('name', 'Unknown')}: Bought {bought:,.0f}, Sold {sold:,.0f}")

                elif "cik" in data:  # Company info
                    lines.append(f"Company: {data.get('name', 'Unknown')} ({data.get('ticker', 'Unknown')})")
                    lines.append(f"  CIK: {data.get('cik', 'Unknown')}")
                    if data.get("sic_description"):
                        lines.append(f"  Industry: {data.get('sic_description')}")

                else:
                    # Generic formatting
                    for key, value in list(data.items())[:15]:
                        if key not in ["citations", "success"]:
                            lines.append(f"  {key}: {self._format_value(value)}")

            else:
                lines.append(str(data)[:1000])

        return "\n".join(lines)

    def _format_value(self, value: Any) -> str:
        """Format a value for display."""
        if value is None:
            return "N/A"
        if isinstance(value, (int, float)):
            if abs(value) >= 1e12:
                return f"${value/1e12:.2f}T"
            if abs(value) >= 1e9:
                return f"${value/1e9:.2f}B"
            if abs(value) >= 1e6:
                return f"${value/1e6:.2f}M"
            if isinstance(value, float):
                return f"{value:,.2f}"
            return f"{value:,}"
        if isinstance(value, list):
            return f"[{len(value)} items]"
        if isinstance(value, dict):
            return "{...}"
        return str(value)[:100]

    def _fallback_response(self, context: AgentContext) -> str:
        """Generate a basic fallback response."""
        lines = [f"Here's what I found for your query: \"{context.query}\"\n"]

        for result in context.tool_results:
            task_desc = result.get("task_description", "")
            data = result.get("result", {})

            lines.append(f"**{task_desc}:**")

            if isinstance(data, dict):
                if data.get("success") is False:
                    lines.append(f"- Error: {data.get('error', 'Unknown error')}")
                elif "name" in data:
                    lines.append(f"- Company: {data.get('name')} ({data.get('ticker', '')})")
                elif "filings" in data:
                    lines.append(f"- Found {len(data.get('filings', []))} filings")
                else:
                    lines.append("- Data retrieved successfully")
            lines.append("")

        if context.citations:
            lines.append(f"\n**Sources:** {format_citations(context.citations)}")

        return "\n".join(lines)
