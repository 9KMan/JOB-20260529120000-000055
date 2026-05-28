"""Node implementations for the AgentFlow orchestration graph."""

import logging
from typing import Any

from agentflow.orchestrator.state import AgentFlowState

logger = logging.getLogger(__name__)


def router(state: AgentFlowState) -> AgentFlowState:
    """Interprets user intent and builds an execution plan.

    Analyzes the latest user message, determines which subagents should handle
    the request, and creates an execution plan describing agent assignments
    and any parameters needed.

    Args:
        state: Current graph state containing messages and context.

    Returns:
        State update containing the execution_plan and current_agent.
    """
    messages = state.get("messages", [])
    tenant_id = state.get("tenant_id", "")

    if not messages:
        return {"execution_plan": None, "current_agent": None, "error": "No messages to process"}

    latest_message = messages[-1]
    user_content = latest_message.get("content", "") if isinstance(latest_message, dict) else str(latest_message)

    # Placeholder routing logic - in production this would use LLM-based intent classification
    plan = {
        "intent": _classify_intent(user_content),
        "agents": _select_agents(user_content),
        "params": {"tenant_id": tenant_id, "user_message": user_content},
    }

    agents = plan.get("agents", [])
    first_agent = agents[0] if agents else None

    logger.info(f"[{tenant_id}] Router selected agents: {agents}")

    return {
        "execution_plan": plan,
        "current_agent": first_agent,
        "retry_count": 0,
        "error": None,
    }


def memory_read(state: AgentFlowState) -> AgentFlowState:
    """Reads relevant context from the vector store (Weaviate).

    Performs a tenant-scoped similarity search to retrieve any relevant
    prior conversations, documents, or context that may help the agent
    respond accurately.

    Args:
        state: Current graph state with tenant_id and messages.

    Returns:
        State update containing retrieved context from vector store.
    """
    tenant_id = state.get("tenant_id", "")
    messages = state.get("messages", [])
    execution_plan = state.get("execution_plan")

    if not tenant_id:
        return {"context": None, "error": "Missing tenant_id for memory read"}

    # Extract query from latest message
    query = ""
    if messages:
        latest = messages[-1]
        query = latest.get("content", "") if isinstance(latest, dict) else str(latest)

    # Placeholder for Weaviate integration
    # In production: results = weaviate_client.query.with_semantic_search(query, tenant_id)
    retrieved_context = {
        "query": query,
        "tenant_id": tenant_id,
        "results": [],
        "message": "Memory read placeholder - integrate Weaviate client here",
    }

    logger.info(f"[{tenant_id}] Memory read completed, retrieved {len(retrieved_context.get('results', []))} items")

    return {"context": retrieved_context}


def agent_dispatch(state: AgentFlowState) -> AgentFlowState:
    """Invokes the appropriate subagent(s) based on the execution plan.

    Dispatches to the current_agent specified in state, passing along
    the execution plan parameters and any retrieved memory context.
    Results are stored in agent_results keyed by agent name.

    Args:
        state: Current graph state with execution_plan and current_agent.

    Returns:
        State update containing agent execution results.
    """
    tenant_id = state.get("tenant_id", "")
    execution_plan = state.get("execution_plan")
    current_agent = state.get("current_agent")
    context = state.get("context")
    agent_results = dict(state.get("agent_results", {}))

    if not current_agent:
        return {"error": "No agent specified for dispatch"}

    params = execution_plan.get("params", {}) if execution_plan else {}
    params["context"] = context

    logger.info(f"[{tenant_id}] Dispatching to agent: {current_agent}")

    # Placeholder agent invocation
    # In production: result = await agent_registry.invoke(current_agent, params)
    result = {
        "agent": current_agent,
        "status": "success",
        "output": f"Placeholder output from {current_agent}",
        "params_received": params,
    }

    agent_results[current_agent] = result

    return {
        "agent_results": agent_results,
        "error": None,
    }


def approval_gate(state: AgentFlowState) -> AgentFlowState:
    """Pauses execution and creates an approval record for human review.

    When triggered, this node creates a database record indicating
    the execution is pending approval. The graph waits at this point
    until an external process approves or rejects the request.

    Args:
        state: Current graph state with execution_plan and agent_results.

    Returns:
        State update with approval_pending=True and approval_record_id.
    """
    tenant_id = state.get("tenant_id", "")
    execution_plan = state.get("execution_plan")
    agent_results = state.get("agent_results", {})

    # Check if approval is needed based on plan metadata
    requires_approval = execution_plan.get("requires_approval", False) if execution_plan else False

    if not requires_approval:
        logger.info(f"[{tenant_id}] Approval not required, skipping gate")
        return {"approval_pending": False, "approval_record_id": None}

    # Placeholder for database record creation
    # In production: record = db.approval_records.create(tenant_id, execution_plan, agent_results)
    approval_record_id = f"approval_{tenant_id}_{hash(str(execution_plan))}"

    logger.info(f"[{tenant_id}] Approval gate: created record {approval_record_id}")

    return {
        "approval_pending": True,
        "approval_record_id": approval_record_id,
    }


def memory_write(state: AgentFlowState) -> AgentFlowState:
    """Persists agent results and conversation to the vector store.

    Writes the completed agent outputs and relevant context back to
    Weaviate for future retrieval, maintaining tenant-scoped isolation.

    Args:
        state: Current graph state with agent_results and messages.

    Returns:
        State update confirming write completion.
    """
    tenant_id = state.get("tenant_id", "")
    agent_results = state.get("agent_results", {})
    messages = state.get("messages", [])

    if not tenant_id:
        return {"error": "Missing tenant_id for memory write"}

    # Prepare data for vector storage
    write_payload = {
        "tenant_id": tenant_id,
        "agent_results": agent_results,
        "messages": messages,
        "message_count": len(messages),
    }

    # Placeholder for Weaviate write operation
    # In production: weaviate_client.data.insert(write_payload, tenant_id)
    logger.info(f"[{tenant_id}] Memory write completed for {len(agent_results)} agent results")

    return {"context": {"memory_written": True, "payload": write_payload}}


def response_synthesizer(state: AgentFlowState) -> AgentFlowState:
    """Aggregates agent outputs into a coherent final response.

    Takes all agent results and synthesizes them into a unified,
    user-facing response. Handles multiple agents by combining their
    outputs in a logical and readable manner.

    Args:
        state: Current graph state with agent_results and messages.

    Returns:
        State update containing the synthesized response message.
    """
    tenant_id = state.get("tenant_id", "")
    agent_results = state.get("agent_results", {})
    messages = state.get("messages", [])

    if not agent_results:
        synthesized = "I apologize, but I was unable to complete your request."
    else:
        parts = []
        for agent_name, result in agent_results.items():
            output = result.get("output", "") if isinstance(result, dict) else str(result)
            parts.append(f"[{agent_name}]: {output}")

        synthesized = "\n\n".join(parts) if parts else "No results to synthesize."

    # Create the final response message
    response_message = {
        "role": "assistant",
        "content": synthesized,
        "agent_results_count": len(agent_results),
    }

    logger.info(f"[{tenant_id}] Response synthesized from {len(agent_results)} agent results")

    return {
        "messages": response_message,  # Will be added via add_messages reducer
    }