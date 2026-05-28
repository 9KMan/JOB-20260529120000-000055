"""Agent registry for AgentFlow plugin system."""

from agentflow.agents.base import BaseAgent

_registry: dict[str, type[BaseAgent]] = {}


def register(agent_class: type[BaseAgent]) -> type[BaseAgent]:
    """Decorator to register an agent class."""
    _registry[agent_class.name] = agent_class
    return agent_class


class AgentRegistry:
    """Registry for managing available agents."""

    @staticmethod
    def get_agent(name: str) -> BaseAgent | None:
        """Get an agent instance by name."""
        agent_class = _registry.get(name)
        if agent_class:
            return agent_class()
        return None

    @staticmethod
    def list_agents() -> list[type[BaseAgent]]:
        """List all registered agent classes."""
        return list(_registry.values())