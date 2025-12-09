"""Orchestrator for coordinating the multi-agent workflow."""

import logging
import time
from typing import Any

from src.agents.base import AgentContext, AgentResponse, Plan
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
        self.model = model or settings.claude_model
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

        try:
            # Step 1: Planning
            self.logger.info("Phase 1: Planning")
            plan_response = self.planner.run(context)
            if not plan_response.success:
                return f"Failed to create plan: {plan_response.error}"

            # Step 2: Execution
            self.logger.info("Phase 2: Execution")
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
                self.logger.info("Phase 3: Validation")
                val_response = self.validator.run(context)
                if val_response.content and not val_response.content.get("valid", True):
                    self.logger.warning(f"Validation issues: {val_response.content.get('issues')}")

            # Step 4: Synthesis
            self.logger.info("Phase 4: Synthesis")
            synth_response = self.synthesizer.run(context)

            elapsed = time.time() - start_time
            self.logger.info(f"Orchestration complete in {elapsed:.2f}s")

            if synth_response.success:
                return synth_response.content
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


class StreamingOrchestrator(Orchestrator):
    """
    Orchestrator that yields progress updates during execution.

    Useful for CLI/UI that wants to show progress.
    """

    def run_streaming(self, query: str):
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

        try:
            # Phase 1: Planning
            yield ("planning", "Analyzing your query...", None)
            plan_response = self.planner.run(context)

            if not plan_response.success:
                yield ("error", f"Planning failed: {plan_response.error}", None)
                return

            plan: Plan = plan_response.content
            yield ("planned", f"Created plan with {len(plan.tasks)} tasks", plan)

            # Phase 2: Execution
            yield ("executing", "Executing research tasks...", None)

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
                yield ("validating", "Validating results...", None)
                val_response = self.validator.run(context)
                if val_response.content:
                    yield ("validated", "Results validated", val_response.content)

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
