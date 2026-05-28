"""Calendar agent for scheduling meetings."""

from typing import Any

from agentflow.agents.base import BaseAgent
from agentflow.agents.registry import register


@register
class CalendarAgent(BaseAgent):
    """Agent for querying and scheduling meetings."""

    name = "Calendar"
    description = "Query/schedule meetings"
    actions = [
        "query_availability",
        "schedule_meeting",
        "find_slot",
    ]

    def execute(self, context: dict[str, Any], task: str) -> Any:
        """Execute calendar task."""
        return {"status": "executed", "agent": self.name, "task": task}