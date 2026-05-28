"""Plugin manifest for AgentFlow agents."""

AGENT_MANIFEST = [
    {
        "name": "Research",
        "description": "Gather info from web, docs, DB",
        "example_action": "Find my top 10 customers by revenue this quarter",
        "requires_approval": False,
    },
    {
        "name": "Execute",
        "description": "Perform external actions (send email, create CRM record)",
        "example_action": "Create a Stripe invoice for Acme Corp",
        "requires_approval": True,
    },
    {
        "name": "Document",
        "description": "Draft, summarize, transform documents",
        "example_action": "Write a follow-up email based on this ticket",
        "requires_approval": False,
    },
    {
        "name": "Calendar",
        "description": "Query/schedule meetings",
        "example_action": "Schedule a call with Sarah next Tuesday",
        "requires_approval": False,
    },
    {
        "name": "Data",
        "description": "Run queries, compute metrics",
        "example_action": "Show me monthly MRR trend for Q1-Q2",
        "requires_approval": False,
    },
    {
        "name": "Notify",
        "description": "Send alerts via Slack, email, SMS",
        "example_action": "Alert the ops team when inventory drops below threshold",
        "requires_approval": False,
    },
]