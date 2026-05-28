"""Entry point for running the AgentFlow orchestration graph."""

import logging
from typing import Any

from agentflow.orchestrator.graph import get_compiled_graph
from agentflow.orchestrator.state import AgentFlowState, get_initial_state

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run_agentflow(tenant_id: str, messages: list[dict[str, Any]]) -> AgentFlowState:
    """Runs the AgentFlow orchestration graph for a given tenant and conversation.

    This is the main entry point for invoking the orchestration pipeline.
    It initializes the state, compiles the graph, and executes the graph
    with the provided conversation history.

    Args:
        tenant_id: Unique identifier for the tenant/customer.
        messages: List of message dicts with 'role' and 'content' keys.

    Returns:
        Final state after graph execution completes.
    """
    logger.info(f"Starting AgentFlow for tenant: {tenant_id}")

    # Initialize state
    initial_state = get_initial_state(tenant_id)
    initial_state["messages"] = messages

    # Get compiled graph
    graph = get_compiled_graph()

    # Execute the graph
    try:
        final_state = graph.invoke(initial_state)
        logger.info(f"AgentFlow completed for tenant: {tenant_id}")
        return final_state
    except Exception as e:
        logger.error(f"AgentFlow error for tenant {tenant_id}: {e}")
        raise


async def run_agentflow_async(tenant_id: str, messages: list[dict[str, Any]]) -> AgentFlowState:
    """Async version of run_agentflow for use with async frameworks.

    Args:
        tenant_id: Unique identifier for the tenant/customer.
        messages: List of message dicts with 'role' and 'content' keys.

    Returns:
        Final state after graph execution completes.
    """
    logger.info(f"Starting AgentFlow (async) for tenant: {tenant_id}")

    initial_state = get_initial_state(tenant_id)
    initial_state["messages"] = messages

    graph = get_compiled_graph()

    try:
        final_state = await graph.ainvoke(initial_state)
        logger.info(f"AgentFlow completed (async) for tenant: {tenant_id}")
        return final_state
    except Exception as e:
        logger.error(f"AgentFlow error for tenant {tenant_id}: {e}")
        raise


if __name__ == "__main__":
    # Example usage
    example_messages = [
        {"role": "user", "content": "What is the status of my recent orders?"},
    ]

    result = run_agentflow("tenant_123", example_messages)
    print(f"\nFinal messages: {result.get('messages', [])}")
    print(f"Agent results: {result.get('agent_results', {})}")