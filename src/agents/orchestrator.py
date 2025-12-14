"""Orchestrator for coordinating the multi-agent workflow."""

import re
import time
from typing import Any

import structlog

from src.agents.base import AgentContext, Plan, Task, TaskStatus
from src.agents.executor import ExecutorAgent
from src.agents.planner import PlannerAgent
from src.agents.synthesizer import SynthesizerAgent
from src.agents.validator import ValidatorAgent
from src.config import settings
from src.data.ticker_resolver import resolve_ticker

logger = structlog.get_logger()


# Simple query patterns that can bypass the planner
SIMPLE_QUERY_PATTERNS = [
    # Direct revenue queries
    (r"(?:what\s+(?:is|was|were)\s+)?(\w+)(?:'s)?\s+(?:total\s+)?revenue", "get_income_statement"),
    # Net income queries
    (r"(?:what\s+(?:is|was|were)\s+)?(\w+)(?:'s)?\s+net\s+income", "get_income_statement"),
    # EPS queries
    (r"(?:what\s+(?:is|was|were)\s+)?(\w+)(?:'s)?\s+(?:eps|earnings\s+per\s+share)", "get_income_statement"),
    # Operating income
    (r"(?:what\s+(?:is|was|were)\s+)?(\w+)(?:'s)?\s+operating\s+income", "get_income_statement"),
    # Total assets
    (r"(?:what\s+(?:is|was|were)\s+)?(\w+)(?:'s)?\s+(?:total\s+)?assets", "get_balance_sheet"),
    # Total debt
    (r"(?:what\s+(?:is|was|were)\s+)?(\w+)(?:'s)?\s+(?:total\s+)?debt", "get_balance_sheet"),
    # Cash
    (r"(?:what\s+(?:is|was|were)\s+)?(\w+)(?:'s)?\s+(?:cash|cash\s+and\s+equivalents)", "get_balance_sheet"),
    # Cash flow
    (r"(?:what\s+(?:is|was|were)\s+)?(\w+)(?:'s)?\s+(?:operating\s+)?cash\s+flow", "get_cash_flow"),
    # Ticker lookup / company identifier
    (r"(?:what\s+(?:is|was|were)\s+)?(\w+)(?:'s)?\s+(?:ticker\s+symbol|ticker)\b", "get_company_info"),
    # Company info
    (r"(?:tell\s+me\s+about|what\s+is|info\s+(?:on|about)|company\s+info)\s+(\w+)", "get_company_info"),
]


def classify_query_complexity(query: str) -> tuple[str, str | None, str | None, int | None]:
    """
    Classify a query as simple, medium, or complex.

    Returns:
        Tuple of (complexity, ticker, tool_name, year)
        - complexity: 'simple', 'medium', or 'complex'
        - ticker: Extracted ticker if simple
        - tool_name: Suggested tool if simple
        - year: Extracted year if present
    """
    query_lower = query.lower().strip()

    # Complex patterns - always need full planning
    complex_patterns = [
        r"\bcompare\b", r"\bversus\b", r"\bvs\.?\b",
        r"\btrend\b", r"\bover\s+time\b", r"\bhistorical\b",
        r"\brisk\s+factor", r"\bchange[sd]?\b", r"\bdiff",
        r"\bwhy\b", r"\bhow\s+does\b", r"\bexplain\b",
        r"\banalyz", r"\bsummar",
    ]

    for pattern in complex_patterns:
        if re.search(pattern, query_lower):
            return ("complex", None, None, None)

    # Extract year if present
    year_match = re.search(r"\b(20\d{2})\b", query)
    year = int(year_match.group(1)) if year_match else None

    # Check simple patterns
    for pattern, tool_name in SIMPLE_QUERY_PATTERNS:
        match = re.search(pattern, query_lower)
        if match:
            potential_ticker = match.group(1)
            ticker = resolve_ticker(potential_ticker)
            if ticker:
                return ("simple", ticker, tool_name, year)

    # Try to extract ticker for medium complexity
    ticker = None
    words = query.split()
    for word in words:
        clean = re.sub(r"[^A-Za-z]", "", word)
        if clean:
            resolved = resolve_ticker(clean)
            if resolved:
                ticker = resolved
                break

    if ticker:
        return ("medium", ticker, None, year)

    return ("complex", None, None, None)


class Orchestrator:
    """
    Coordinates the multi-agent workflow for financial research.

    Workflow:
    1. Planner analyzes query and creates task plan
    2. Executor runs each task using appropriate tools
    3. Validator checks results (optional for simple queries)
    4. Synthesizer generates final response
    """

    def __init__(self, model: str | None = None):
        """Initialize orchestrator with agent instances sharing the same model."""
        self.model = model or settings.openai_model
        self.planner = PlannerAgent(model)
        self.executor = ExecutorAgent(model)
        self.validator = ValidatorAgent(model)
        self.synthesizer = SynthesizerAgent(model)
        self.max_steps = settings.max_agent_steps
        self.logger = structlog.get_logger()

    def run(self, query: str) -> str:
        """
        Execute the full agent workflow for a query.

        Args:
            query: User's natural language query

        Returns:
            Synthesized response string
        """
        start_time = time.time()
        query_preview = query[:80] + "..." if len(query) > 80 else query

        # Pre-classify query complexity for latency optimization
        complexity, ticker, tool_hint, year = classify_query_complexity(query)

        self.logger.info(
            "Orchestration started",
            query=query_preview,
            query_length=len(query),
            complexity=complexity,
            ticker=ticker,
            max_steps=self.max_steps,
        )

        # Initialize context
        context = AgentContext(
            query=query,
            max_steps=self.max_steps,
        )

        max_retries = 3
        retries = 0

        try:
            # FAST PATH: For simple queries, skip the planner LLM call
            if complexity == "simple" and ticker and tool_hint:
                phase_start = time.time()
                self.logger.info(
                    "Fast path: Skipping planner for simple query",
                    ticker=ticker,
                    tool=tool_hint,
                    year=year,
                )

                # Build plan directly without LLM call
                import uuid
                task = Task(
                    id=f"task_{uuid.uuid4().hex[:8]}",
                    description=f"Get {tool_hint.replace('_', ' ')} for {ticker}",
                    tool_hint=tool_hint,
                    status=TaskStatus.PENDING,
                )
                context.plan = Plan(
                    query=query,
                    reasoning=f"Simple query for {ticker} {tool_hint}",
                    tasks=[task],
                    is_simple=True,
                )

                phase_elapsed = time.time() - phase_start
                self.logger.info(
                    "Phase 1: Fast path planning completed",
                    task_count=1,
                    is_simple=True,
                    elapsed_seconds=round(phase_elapsed, 2),
                )
            else:
                # STANDARD PATH: Use the planner LLM
                phase_start = time.time()
                self.logger.info("Phase 1: Planning started")
                plan_response = self.planner.run(context)
                phase_elapsed = time.time() - phase_start

                if not plan_response.success:
                    self.logger.error(
                        "Planning failed",
                        error=plan_response.error,
                        elapsed_seconds=round(phase_elapsed, 2),
                    )
                    return f"Failed to create plan: {plan_response.error}"

                self.logger.info(
                    "Phase 1: Planning completed",
                    task_count=len(context.plan.tasks) if context.plan else 0,
                    is_simple=context.plan.is_simple if context.plan else True,
                    elapsed_seconds=round(phase_elapsed, 2),
                )

            task_count = len(context.plan.tasks) if context.plan else 0
            task_count = len(context.plan.tasks) if context.plan else 0

            # Validation retry loop
            while retries < max_retries:
                # Step 2: Execution
                phase_start = time.time()
                attempt_msg = f" (attempt {retries + 1}/{max_retries})" if retries > 0 else ""
                self.logger.info(f"Phase 2: Execution started{attempt_msg}")

                while context.step_count < context.max_steps:
                    exec_response = self.executor.run(context)

                    if not exec_response.should_continue:
                        break

                    if not exec_response.success:
                        self.logger.warning(
                            "Execution step failed",
                            error=exec_response.error,
                            step=context.step_count,
                        )
                        # Continue with other tasks if possible
                        continue

                exec_elapsed = time.time() - phase_start
                completed_tasks = sum(1 for t in context.plan.tasks if t.status.value == "completed") if context.plan else 0
                self.logger.info(
                    "Phase 2: Execution completed",
                    completed_tasks=completed_tasks,
                    total_tasks=task_count,
                    steps_used=context.step_count,
                    elapsed_seconds=round(exec_elapsed, 2),
                )

                # Step 3: Validation (skip for simple queries)
                if context.plan and not context.plan.is_simple:
                    val_phase_start = time.time()
                    self.logger.info(f"Phase 3: Validation started{attempt_msg}")
                    val_response = self.validator.run(context)
                    val_elapsed = time.time() - val_phase_start

                    if val_response.content and not val_response.content.get("valid", True):
                        issues = val_response.content.get("issues", [])
                        suggestions = val_response.content.get("suggestions", [])
                        confidence = val_response.content.get("confidence", 0.0)

                        self.logger.warning(
                            "Validation failed",
                            attempt=retries + 1,
                            max_retries=max_retries,
                            confidence=round(confidence, 2),
                            issues=issues,
                            elapsed_seconds=round(val_elapsed, 2),
                        )

                        # Add correction tasks and retry
                        if retries < max_retries - 1:  # Don't add corrections on last attempt
                            self._add_correction_tasks(context, issues, suggestions)
                            retries += 1
                            continue
                        else:
                            self.logger.warning("Max retries reached, proceeding with current results")
                    else:
                        self.logger.info(
                            "Phase 3: Validation passed",
                            elapsed_seconds=round(val_elapsed, 2),
                        )

                # Validation passed or not needed
                break

            # Step 4: Synthesis
            synth_start = time.time()
            self.logger.info("Phase 4: Synthesis started")
            synth_response = self.synthesizer.run(context)
            synth_elapsed = time.time() - synth_start

            elapsed = time.time() - start_time
            self.logger.info(
                "Orchestration completed",
                total_elapsed_seconds=round(elapsed, 2),
                synthesis_elapsed_seconds=round(synth_elapsed, 2),
                tool_results_count=len(context.tool_results),
                citations_count=len(context.citations),
            )

            if synth_response.success:
                return str(synth_response.content)
            else:
                return f"Failed to synthesize response: {synth_response.error}"

        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.exception(
                "Orchestration failed",
                error=str(e),
                error_type=type(e).__name__,
                elapsed_seconds=round(elapsed, 2),
            )
            return f"An error occurred while processing your query: {str(e)}"

    def run_simple(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a single tool directly without the full agent workflow.

        Useful for CLI commands and simple queries.
        """
        from src.tools import registry

        result = registry.execute(tool_name, args)
        return {
            "success": result.success,
            "result": result.result,
            "error": result.error,
            "citations": [str(c) for c in result.citations],
        }

    def _add_correction_tasks(
        self,
        context: AgentContext,
        issues: list[str],
        suggestions: list[str],
    ) -> None:
        """
        Add correction tasks to the plan based on validation feedback.

        Args:
            context: Current agent context
            issues: List of validation issues identified
            suggestions: List of suggestions for fixing the issues
        """
        from src.agents.base import Task, TaskStatus

        if not context.plan:
            return

        initial_task_count = len(context.plan.tasks)

        # Create correction tasks from suggestions
        for i, suggestion in enumerate(suggestions):
            correction_task = Task(
                id=f"correction_{initial_task_count + i + 1}",
                description=f"Correction: {suggestion}",
                tool_hint=None,  # Let executor determine best tool
                status=TaskStatus.PENDING,
                dependencies=[],
            )
            context.plan.tasks.append(correction_task)
            self.logger.info(f"Added correction task: {suggestion}")

        # If no suggestions provided, create a generic retry task from issues
        if not suggestions and issues:
            # Take up to 2 issues to keep the task description manageable
            issue_summary = "; ".join(issues[:2])
            correction_task = Task(
                id=f"correction_{initial_task_count + 1}",
                description=f"Address validation issues: {issue_summary}",
                tool_hint=None,
                status=TaskStatus.PENDING,
                dependencies=[],
            )
            context.plan.tasks.append(correction_task)
            self.logger.info(f"Added generic correction task for issues: {issue_summary}")

        added_count = len(context.plan.tasks) - initial_task_count
        self.logger.info(f"Added {added_count} correction task(s) to plan")


class StreamingOrchestrator(Orchestrator):
    """
    Orchestrator that yields progress updates during execution.

    Useful for CLI/UI that wants to show progress.
    """

    def run_streaming(self, query: str) -> Any:  # noqa: ANN401
        """
        Execute workflow with streaming progress updates.

        Yields:
            Tuple of (phase, message, data)
        """
        start_time = time.time()
        self.logger.info(f"Starting streaming orchestration for: {query}")

        context = AgentContext(
            query=query,
            max_steps=self.max_steps,
        )

        max_retries = 3
        retries = 0

        try:
            # Phase 1: Planning
            yield ("planning", "Analyzing your query...", None)
            plan_response = self.planner.run(context)

            if not plan_response.success:
                yield ("error", f"Planning failed: {plan_response.error}", None)
                return

            plan: Plan = plan_response.content
            yield ("planned", f"Created plan with {len(plan.tasks)} tasks", plan)

            # Validation retry loop
            while retries < max_retries:
                # Phase 2: Execution
                attempt_msg = f" (attempt {retries + 1}/{max_retries})" if retries > 0 else ""
                yield ("executing", f"Executing research tasks{attempt_msg}...", None)

                while context.step_count < context.max_steps:
                    # Find the next task to execute
                    if not context.plan:
                        break

                    next_task = None
                    for task in context.plan.tasks:
                        if task.status.value in ["pending", "in_progress"]:
                            next_task = task
                            break

                    # Show what we're about to do
                    if next_task and next_task.status.value == "pending":
                        tool_hint = next_task.tool_hint or "unknown tool"
                        yield (
                            "tool_start",
                            f"🔧 Calling {tool_hint}: {next_task.description}",
                            {
                                "task_id": next_task.id,
                                "description": next_task.description,
                                "tool": tool_hint,
                            },
                        )

                    exec_response = self.executor.run(context)

                    if context.tool_results:
                        last_result = context.tool_results[-1]
                        yield (
                            "task_complete",
                            f"✅ Completed: {last_result['task_description']}",
                            last_result,
                        )

                    if not exec_response.should_continue:
                        break

                # Phase 3: Validation (conditional)
                if context.plan and not context.plan.is_simple:
                    yield ("validating", f"Validating results{attempt_msg}...", None)
                    val_response = self.validator.run(context)

                    if val_response.content:
                        is_valid = val_response.content.get("valid", True)
                        if is_valid:
                            yield ("validated", "Results validated", val_response.content)
                        else:
                            issues = val_response.content.get("issues", [])
                            suggestions = val_response.content.get("suggestions", [])
                            confidence = val_response.content.get("confidence", 0.0)

                            yield (
                                "validation_failed",
                                f"Validation failed (confidence={confidence:.2f})",
                                {"issues": issues, "suggestions": suggestions, "attempt": retries + 1},
                            )

                            # Add correction tasks and retry
                            if retries < max_retries - 1:
                                self._add_correction_tasks(context, issues, suggestions)
                                yield (
                                    "retrying",
                                    "Adding correction tasks and retrying...",
                                    {"correction_count": len(suggestions) or 1},
                                )
                                retries += 1
                                continue
                            else:
                                yield (
                                    "warning",
                                    "Max retries reached, proceeding with current results",
                                    None,
                                )

                # Validation passed or not needed
                break

            # Phase 4: Synthesis
            yield ("synthesizing", "Generating response...", None)
            synth_response = self.synthesizer.run(context)

            elapsed = time.time() - start_time

            if synth_response.success:
                yield ("complete", synth_response.content, {"elapsed": elapsed})
            else:
                yield ("error", f"Synthesis failed: {synth_response.error}", None)

        except Exception as e:
            self.logger.exception(f"Streaming orchestration failed: {e}")
            yield ("error", f"Error: {str(e)}", None)


# Global orchestrator instance
_orchestrator: Orchestrator | None = None


def get_orchestrator() -> Orchestrator:
    """Get or create the global orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator
