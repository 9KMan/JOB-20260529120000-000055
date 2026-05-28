"""Document agent for drafting and summarizing."""

from typing import Any

from agentflow.agents.base import BaseAgent
from agentflow.agents.registry import register


@register
class DocumentAgent(BaseAgent):
    """Agent for drafting, summarizing, and transforming documents."""

    name = "Document"
    description = "Draft, summarize, transform documents"
    actions = [
        "draft_email",
        "summarize",
        "transform",
        "write_followup",
    ]

    def execute(self, context: dict[str, Any], task: str) -> Any:
        """Execute document task."""
        if "follow-up email" in task.lower() or "followup email" in task.lower():
            return self._write_followup_email(context, task)
        return {"status": "executed", "agent": self.name, "task": task}

    def _write_followup_email(self, context: dict[str, Any], task: str) -> Any:
        """Example action: Write follow-up email based on ticket."""
        return {
            "status": "success",
            "action": "Write follow-up email",
            "draft": "Hi,\n\nThank you for reaching out regarding your inquiry. "
                     "I wanted to follow up on our previous conversation...\n\nBest regards",
        }