"""Research agent for information gathering."""

from typing import Any

from agentflow.agents.base import BaseAgent
from agentflow.agents.registry import register


@register
class ResearchAgent(BaseAgent):
    """Agent for gathering information from web, docs, and databases."""

    name = "Research"
    description = "Gather info from web, docs, DB"
    actions = [
        "web_search",
        "doc_retrieval",
        "db_query",
        "find_customers",
    ]

    def execute(self, context: dict[str, Any], task: str) -> Any:
        """Execute research task using tool-like interface."""
        # Tool interface for: web search, doc retrieval, DB queries
        if "find top customers" in task.lower():
            return self._find_top_customers(context, task)
        return {"status": "executed", "agent": self.name, "task": task}

    def _find_top_customers(self, context: dict[str, Any], task: str) -> Any:
        """Example action: Find top customers by revenue."""
        return {
            "status": "success",
            "action": "Find top customers by revenue",
            "results": [
                {"name": "Acme Corp", "revenue": 150000},
                {"name": "Globex", "revenue": 120000},
                {"name": "Initech", "revenue": 95000},
            ],
        }