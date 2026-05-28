"""Data agent for running queries and computing metrics."""

from typing import Any

from agentflow.agents.base import BaseAgent
from agentflow.agents.registry import register


@register
class DataAgent(BaseAgent):
    """Agent for running queries and computing metrics."""

    name = "Data"
    description = "Run queries, compute metrics"
    actions = [
        "run_query",
        "compute_metric",
        "mrr_trend",
    ]

    def execute(self, context: dict[str, Any], task: str) -> Any:
        """Execute data task."""
        return {"status": "executed", "agent": self.name, "task": task}