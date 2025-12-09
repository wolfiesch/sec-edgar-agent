"""Base agent class and common types for the SEC EDGAR Agent system."""

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from anthropic import Anthropic
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

    query: str = Field(description="Original user query")
    plan: Plan | None = Field(default=None)
    tool_results: list[dict[str, Any]] = Field(default_factory=list)
    conversation_history: list[dict[str, Any]] = Field(default_factory=list)
    citations: list[Any] = Field(default_factory=list)
    step_count: int = Field(default=0)
    max_steps: int = Field(default=20)

    class Config:
        arbitrary_types_allowed = True


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
        self.role = role
        self.model = model or settings.claude_model
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.logger = logging.getLogger(f"{__name__}.{role.value}")

    @abstractmethod
    def run(self, context: AgentContext) -> AgentResponse:
        """Execute the agent's task."""
        pass

    def _call_claude(
        self,
        system_prompt: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """Make a call to Claude API."""
        try:
            kwargs: dict[str, Any] = {
                "model": self.model,
                "max_tokens": max_tokens,
                "system": system_prompt,
                "messages": messages,
            }

            if tools:
                kwargs["tools"] = tools

            response = self.client.messages.create(**kwargs)

            return {
                "content": response.content,
                "stop_reason": response.stop_reason,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
            }

        except Exception as e:
            self.logger.error(f"Claude API call failed: {e}")
            raise

    def _extract_text(self, content: list[Any]) -> str:
        """Extract text from Claude response content blocks."""
        text_parts = []
        for block in content:
            if hasattr(block, "text"):
                text_parts.append(block.text)
        return "\n".join(text_parts)

    def _extract_tool_use(self, content: list[Any]) -> list[dict[str, Any]]:
        """Extract tool use blocks from Claude response."""
        tool_uses = []
        for block in content:
            if hasattr(block, "type") and block.type == "tool_use":
                tool_uses.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })
        return tool_uses
