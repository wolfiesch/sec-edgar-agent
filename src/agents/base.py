"""Base agent class and common types for the SEC EDGAR Agent system."""

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from openai import OpenAI
from pydantic import BaseModel, Field

from src.config import settings

logger = logging.getLogger(__name__)


class AgentRole(str, Enum):
    """Agent roles in the system."""

    PLANNER = "planner"
    EXECUTOR = "executor"
    VALIDATOR = "validator"
    SYNTHESIZER = "synthesizer"


class TaskStatus(str, Enum):
    """Status of a task in the workflow."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_VALIDATION = "needs_validation"


class Task(BaseModel):
    """A task to be executed by the agent system."""

    id: str = Field(description="Unique task identifier")
    description: str = Field(description="What needs to be done")
    tool_hint: str | None = Field(default=None, description="Suggested tool to use")
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    result: Any | None = Field(default=None, description="Task result")
    error: str | None = Field(default=None, description="Error message if failed")
    dependencies: list[str] = Field(default_factory=list, description="Task IDs this depends on")


class Plan(BaseModel):
    """A plan consisting of multiple tasks."""

    query: str = Field(description="Original user query")
    reasoning: str = Field(description="Why this plan was chosen")
    tasks: list[Task] = Field(default_factory=list)
    is_simple: bool = Field(default=False, description="Whether this is a simple single-tool query")


class AgentContext(BaseModel):
    """Context passed between agents during execution."""

    model_config = {"arbitrary_types_allowed": True}

    query: str = Field(description="Original user query")
    plan: Plan | None = Field(default=None)
    tool_results: list[dict[str, Any]] = Field(default_factory=list)
    conversation_history: list[dict[str, Any]] = Field(default_factory=list)
    citations: list[Any] = Field(default_factory=list)
    step_count: int = Field(default=0)
    max_steps: int = Field(default=20)


class AgentResponse(BaseModel):
    """Response from an agent."""

    success: bool = Field(description="Whether the agent succeeded")
    content: Any = Field(description="Agent output")
    error: str | None = Field(default=None)
    should_continue: bool = Field(default=True, description="Whether workflow should continue")


class BaseAgent(ABC):
    """Base class for all agents in the system."""

    def __init__(
        self,
        role: AgentRole,
        model: str | None = None,
    ):
        """
        Initialize an agent with its role and backing LLM model.

        Args:
            role: The role this agent plays in the system (e.g., PLANNER, EXECUTOR).
            model: The LLM model to use (defaults to settings.openai_model).
        """
        self.role = role
        self.model = model or settings.openai_model
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.logger = logging.getLogger(f"{__name__}.{role.value}")

    @abstractmethod
    def run(self, context: AgentContext) -> AgentResponse:
        """
        Execute the agent's task.

        Args:
            context: Shared context containing query, plan, and history.

        Returns:
            AgentResponse containing success status and content.
        """
        pass

    def _call_llm(
        self,
        system_prompt: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """
        Make a call to OpenAI API.

        Args:
            system_prompt: System prompt defining the agent's persona.
            messages: List of conversation messages.
            tools: Optional list of tool definitions.
            max_tokens: Maximum tokens for response (default: 4096).

        Returns:
            Dictionary containing content, tool_calls, finish_reason, and usage stats.
        """
        try:
            # Add system message to messages list (OpenAI format)
            full_messages = [{"role": "system", "content": system_prompt}] + messages

            kwargs: dict[str, Any] = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": full_messages,
            }

            if tools:
                kwargs["tools"] = tools

            response = self.client.chat.completions.create(**kwargs)

            # Extract message from response
            message = response.choices[0].message

            return {
                "content": message.content,
                "tool_calls": message.tool_calls,
                "finish_reason": response.choices[0].finish_reason,
                "usage": {
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                },
            }

        except Exception as e:
            self.logger.error(f"OpenAI API call failed: {e}")
            raise

    def _extract_text(self, content: str | None) -> str:
        """Extract text from OpenAI response content."""
        return content or ""

    def _extract_tool_calls(self, tool_calls: list[Any] | None) -> list[dict[str, Any]]:
        """
        Extract tool calls from OpenAI response.

        Args:
            tool_calls: List of tool call objects from OpenAI response.

        Returns:
            List of dictionaries with tool id, name, and parsed arguments.
        """
        if not tool_calls:
            return []

        extracted = []
        for tool_call in tool_calls:
            if hasattr(tool_call, "function"):
                import json
                extracted.append({
                    "id": tool_call.id,
                    "name": tool_call.function.name,
                    "input": json.loads(tool_call.function.arguments),
                })
        return extracted
