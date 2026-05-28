"""Base agent abstract class for AgentFlow."""

from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    name: str
    description: str
    actions: list[str]

    @abstractmethod
    def execute(self, context: dict[str, Any], task: str) -> Any:
        """Execute the agent's task with the given context."""
        pass

    def requires_approval(self) -> bool:
        """Whether this agent needs human approval before external actions."""
        return False