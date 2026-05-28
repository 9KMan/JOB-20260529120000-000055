"""Notify agent for sending alerts."""

from typing import Any

from agentflow.agents.base import BaseAgent
from agentflow.agents.registry import register


@register
class NotifyAgent(BaseAgent):
    """Agent for sending alerts via Slack, email, SMS."""

    name = "Notify"
    description = "Send alerts via Slack, email, SMS"
    actions = [
        "send_slack",
        "send_email",
        "send_sms",
        "alert_threshold",
    ]

    def execute(self, context: dict[str, Any], task: str) -> Any:
        """Execute notification task."""
        return {"status": "executed", "agent": self.name, "task": task}