"""LangGraph state definition for AgentFlow orchestration."""

from typing import Annotated, TypedDict

from langgraph.graph import add_messages


class AgentFlowState(TypedDict, total=False):
    """State schema for the AgentFlow orchestration graph.

    Attributes:
        tenant_id: Unique identifier for the tenant/customer.
        messages: Conversation history messages.
        agent_results: Results from dispatched subagents.
        approval_pending: Whether execution is paused waiting for approval.
        approval_record_id: Database record ID for the pending approval.
        execution_plan: Plan created by router describing what agents to invoke.
        current_agent: Name of the agent currently being dispatched.
        retry_count: Number of times the current agent has been retried.
        max_retries: Maximum number of retries allowed per agent.
        error: Error message if any step failed.
        context: Additional context data (e.g., from memory_read).
    """

    tenant_id: str
    messages: Annotated[list[dict], add_messages]
    agent_results: dict[str, dict]
    approval_pending: bool
    approval_record_id: str | None
    execution_plan: dict | None
    current_agent: str | None
    retry_count: int
    max_retries: int
    error: str | None
    context: dict | None


def get_initial_state(tenant_id: str) -> AgentFlowState:
    """Factory function to create initial state for a new conversation.

    Args:
        tenant_id: The tenant identifier.

    Returns:
        Initial state dictionary with defaults.
    """
    return AgentFlowState(
        tenant_id=tenant_id,
        messages=[],
        agent_results={},
        approval_pending=False,
        approval_record_id=None,
        execution_plan=None,
        current_agent=None,
        retry_count=0,
        max_retries=3,
        error=None,
        context=None,
    )