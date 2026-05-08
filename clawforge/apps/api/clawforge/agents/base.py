"""Base agent class for all ClawForge agents."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class AgentResult(BaseModel):
    """Result from agent execution."""

    success: bool
    output: Any
    error: str | None = None
    cost_cents: int = 0
    tokens_used: int = 0


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    name: str = "base"
    description: str = "Base agent"

    @abstractmethod
    async def execute(self, input_data: dict[str, Any]) -> AgentResult:
        """Execute the agent's task.

        Args:
            input_data: Input data for the agent

        Returns:
            AgentResult with success status, output, and cost info
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name}>"
