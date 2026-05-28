"""LangGraph state graph for AgentFlow orchestration."""

from langgraph.graph import StateGraph

from agentflow.orchestrator.edges import (
    continue_after_router,
    route_after_dispatch,
    should_retry_or_skip,
)
from agentflow.orchestrator.nodes import (
    agent_dispatch,
    approval_gate,
    memory_read,
    memory_write,
    response_synthesizer,
    router,
)
from agentflow.orchestrator.state import AgentFlowState, get_initial_state


def create_agentflow_graph() -> StateGraph:
    """Creates and configures the AgentFlow orchestration graph.

    The graph consists of the following nodes:
        - router: Interprets user intent and builds execution plan
        - memory_read: Reads relevant context from vector store
        - agent_dispatch: Invokes appropriate subagents
        - approval_gate: Pauses for human approval when required
        - memory_write: Persists results to vector store
        - response_synthesizer: Aggregates agent outputs

    Edges:
        - START -> router
        - router -> memory_read (on success) or response_synthesizer (on error)
        - memory_read -> agent_dispatch
        - agent_dispatch -> approval_gate (if approval required) or memory_write
        - approval_gate -> agent_dispatch (retry) or response_synthesizer (skip)
        - memory_write -> response_synthesizer
        - response_synthesizer -> END

    Returns:
        Configured StateGraph instance ready to be compiled.
    """
    # Initialize the graph with our state schema
    graph = StateGraph(AgentFlowState)

    # Register all nodes
    graph.add_node("router", router)
    graph.add_node("memory_read", memory_read)
    graph.add_node("agent_dispatch", agent_dispatch)
    graph.add_node("approval_gate", approval_gate)
    graph.add_node("memory_write", memory_write)
    graph.add_node("response_synthesizer", response_synthesizer)

    # Set entry point
    graph.set_entry_point("router")

    # Add conditional edges from router
    graph.add_conditional_edges(
        "router",
        continue_after_router,
        {
            "memory_read": "memory_read",
            "response_synthesizer": "response_synthesizer",
        },
    )

    # memory_read always runs before agent_dispatch
    graph.add_edge("memory_read", "agent_dispatch")

    # Add conditional edges from agent_dispatch
    graph.add_conditional_edges(
        "agent_dispatch",
        route_after_dispatch,
        {
            "approval_gate": "approval_gate",
            "memory_write": "memory_write",
        },
    )

    # Add conditional edges from approval_gate (retry loop)
    graph.add_conditional_edges(
        "approval_gate",
        should_retry_or_skip,
        {
            "agent_dispatch": "agent_dispatch",
            "response_synthesizer": "response_synthesizer",
        },
    )

    # memory_write leads to response_synthesizer
    graph.add_edge("memory_write", "response_synthesizer")

    # Set finish point
    graph.set_finish_point("response_synthesizer")

    return graph


def get_compiled_graph():
    """Returns a compiled version of the AgentFlow graph.

    This is the main entry point for running the orchestration graph.

    Returns:
        Compiled StateGraph that can be invoked with graph.invoke().
    """
    graph = create_agentflow_graph()
    return graph.compile()