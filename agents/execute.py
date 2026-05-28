"""Execute agent for external actions."""

from typing import Any

from agentflow.agents.base import BaseAgent
from agentflow.agents.registry import register


@register
class ExecuteAgent(BaseAgent):
    """Agent for performing external actions."""

    name = "Execute"
    description = "Perform external actions (send email, create CRM record)"
    actions = [
        "send_email",
        "create_crm_record",
        "create_invoice",
        "api_call",
    ]

    def execute(self, context: dict[str, Any], task: str) -> Any:
        """Execute external action task."""
        if "stripe invoice" in task.lower() or "create invoice" in task.lower():
            return self._create_stripe_invoice(context, task)
        return {"status": "executed", "agent": self.name, "task": task}

    def requires_approval(self) -> bool:
        """External actions require human approval."""
        return True

    def _create_stripe_invoice(self, context: dict[str, Any], task: str) -> Any:
        """Example action: Create a Stripe invoice."""
        return {
            "status": "pending_approval",
            "action": "Create Stripe invoice",
            "target": "Acme Corp",
            "message": "Human approval required for external action",
        }