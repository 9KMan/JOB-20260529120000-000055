"""Conditional edge logic for the AgentFlow orchestration graph."""

from typing import Literal

from agentflow.orchestrator.state import AgentFlowState


def should_retry_or_skip(state: AgentFlowState) -> Literal["agent_dispatch", "response_synthesizer"]:
    """Determines whether to retry agent dispatch or skip to response synthesis.

    This is the conditional edge function from approval_gate. If the approval
    record indicates the action was approved, retry the agent dispatch with
    incremented retry count. If skipped/rejected, proceed to synthesize response.

    In practice, approval_pending=False here means the approval gate was bypassed
    (not required) or the user approved, so we continue to either retry or
    synthesize based on retry count.

    Args:
        state: Current graph state.

    Returns:
        "agent_dispatch" to retry, or "response_synthesizer" to skip.
    """
    tenant_id = state.get("tenant_id", "")
    approval_pending = state.get("approval_pending", False)
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)
    error = state.get("error")

    # If there's an error that requires retry
    if error and retry_count < max_retries:
        return "agent_dispatch"

    # If approval is still pending, something went wrong - proceed to synthesize
    if approval_pending:
        return "response_synthesizer"

    # Check if we should retry based on execution plan metadata
    execution_plan = state.get("execution_plan")
    if execution_plan:
        # If plan indicates this should be retried and we haven't exceeded max_retries
        should_retry_plan = execution_plan.get("should_retry", False)
        if should_retry_plan and retry_count < max_retries:
            return "agent_dispatch"

    # Default: proceed to response synthesis
    return "response_synthesizer"


def route_after_dispatch(state: AgentFlowState) -> Literal["approval_gate", "memory_write"]:
    """Routes to either approval_gate or memory_write after agent_dispatch.

    Args:
        state: Current graph state.

    Returns:
        "approval_gate" if approval is required, otherwise "memory_write".
    """
    execution_plan = state.get("execution_plan")

    if execution_plan and execution_plan.get("requires_approval", False):
        return "approval_gate"

    return "memory_write"


def continue_after_router(state: AgentFlowState) -> Literal["memory_read", "response_synthesizer"]:
    """Routes to memory_read after router, or response_synthesizer on error.

    Args:
        state: Current graph state.

    Returns:
        "memory_read" to continue normal flow, or "response_synthesizer" on error.
    """
    error = state.get("error")
    execution_plan = state.get("execution_plan")

    if error or not execution_plan:
        return "response_synthesizer"

    return "memory_read"