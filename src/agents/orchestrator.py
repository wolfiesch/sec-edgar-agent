"""Orchestrator for coordinating the multi-agent workflow."""

import logging
import time
from typing import Any

from src.agents.base import AgentContext, Plan
from src.agents.executor import ExecutorAgent
from src.agents.planner import PlannerAgent
from src.agents.synthesizer import SynthesizerAgent
from src.agents.validator import ValidatorAgent
from src.config import settings

logger = logging.getLogger(__name__)


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
        self.model = model or settings.openai_model
        self.planner = PlannerAgent(model)
        self.executor = ExecutorAgent(model)
        self.validator = ValidatorAgent(model)
        self.synthesizer = SynthesizerAgent(model)
        self.max_steps = settings.max_agent_steps
        self.logger = logging.getLogger(__name__)

    def run(self, query: str) -> str:
        """
        Execute the full agent workflow for a query.

        Args:
            query: User's natural language query

        Returns:
            Synthesized response string
        """
        start_time = time.time()
        self.logger.info(f"Starting orchestration for: {query}")

        # Initialize context
        context = AgentContext(
            query=query,
            max_steps=self.max_steps,
        )

        max_retries = 3
        retries = 0

        try:
            # Step 1: Planning
            self.logger.info("Phase 1: Planning")
            plan_response = self.planner.run(context)
            if not plan_response.success:
                return f"Failed to create plan: {plan_response.error}"

            # Validation retry loop
            while retries < max_retries:
                # Step 2: Execution
                attempt_msg = f" (attempt {retries + 1}/{max_retries})" if retries > 0 else ""
                self.logger.info(f"Phase 2: Execution{attempt_msg}")

                while context.step_count < context.max_steps:
                    exec_response = self.executor.run(context)

                    if not exec_response.should_continue:
                        break

                    if not exec_response.success:
                        self.logger.warning(f"Execution step failed: {exec_response.error}")
                        # Continue with other tasks if possible
                        continue

                # Step 3: Validation (skip for simple queries)
                if context.plan and not context.plan.is_simple:
                    self.logger.info(f"Phase 3: Validation{attempt_msg}")
                    val_response = self.validator.run(context)

                    if val_response.content and not val_response.content.get("valid", True):
                        issues = val_response.content.get("issues", [])
                        suggestions = val_response.content.get("suggestions", [])
                        confidence = val_response.content.get("confidence", 0.0)

                        self.logger.warning(
                            f"Validation failed (attempt {retries + 1}/{max_retries}): "
                            f"confidence={confidence:.2f}, issues={issues}"
                        )

                        # Add correction tasks and retry
                        if retries < max_retries - 1:  # Don't add corrections on last attempt
                            self._add_correction_tasks(context, issues, suggestions)
                            retries += 1
                            continue
                        else:
                            self.logger.warning("Max retries reached, proceeding with current results")

                # Validation passed or not needed
                break

            # Step 4: Synthesis
            self.logger.info("Phase 4: Synthesis")
            synth_response = self.synthesizer.run(context)

            elapsed = time.time() - start_time
            self.logger.info(f"Orchestration complete in {elapsed:.2f}s")

            if synth_response.success:
                return str(synth_response.content)
            else:
                return f"Failed to synthesize response: {synth_response.error}"

        except Exception as e:
            self.logger.exception(f"Orchestration failed: {e}")
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
                    exec_response = self.executor.run(context)

                    if context.tool_results:
                        last_result = context.tool_results[-1]
                        yield (
                            "task_complete",
                            f"Completed: {last_result['task_description']}",
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
