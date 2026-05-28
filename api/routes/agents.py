"""Agent routes - list and manage registered agents."""
from fastapi import APIRouter, HTTPException, status, Request
from typing import List, Optional
from datetime import datetime

from ..models import Agent, AgentStatus
from ..middleware.tenant import get_tenant_id

router = APIRouter(prefix="/agents", tags=["agents"])

# In-memory registry for demo
agents_registry = {
    "chat-agent": {
        "name": "chat-agent",
        "description": "General purpose chat agent forConversational interactions",
        "version": "1.0.0",
        "status": AgentStatus.ACTIVE,
        "capabilities": ["chat", "streaming", "multilingual"],
        "endpoint": "http://localhost:8001"
    },
    "code-agent": {
        "name": "code-agent",
        "description": "Agent specialized in code review and generation",
        "version": "1.2.0",
        "status": AgentStatus.ACTIVE,
        "capabilities": ["code-review", "code-generation", "refactoring"],
        "endpoint": "http://localhost:8002"
    },
    "data-agent": {
        "name": "data-agent",
        "description": "Agent for data processing and analytics",
        "version": "0.9.0",
        "status": AgentStatus.ACTIVE,
        "capabilities": ["data-processing", "analytics", "visualization"],
        "endpoint": "http://localhost:8003"
    },
    "approval-agent": {
        "name": "approval-agent",
        "description": "Agent for handling approval workflows",
        "version": "1.0.0",
        "status": AgentStatus.ACTIVE,
        "capabilities": ["approval-workflow", "notifications", "escalation"],
        "endpoint": "http://localhost:8004"
    }
}


@router.get("/", response_model=List[Agent])
async def list_agents(
    request: Request,
    status_filter: Optional[AgentStatus] = None,
    capability: Optional[str] = None
):
    """
    List all registered agents.

    Args:
        status_filter: Optional filter by agent status
        capability: Optional filter by capability

    Returns:
        List of agents matching the filters
    """
    tenant_id = get_tenant_id(request)

    agents = []
    for agent_data in agents_registry.values():
        # Apply status filter
        if status_filter and agent_data["status"] != status_filter:
            continue

        # Apply capability filter
        if capability and capability not in agent_data["capabilities"]:
            continue

        agents.append(Agent(**agent_data))

    return agents


@router.get("/{name}", response_model=Agent)
async def get_agent(name: str, request: Request):
    """
    Get details for a specific agent.

    Args:
        name: Agent name/identifier

    Returns:
        Agent details
    """
    tenant_id = get_tenant_id(request)

    if name not in agents_registry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{name}' not found"
        )

    return Agent(**agents_registry[name])


@router.post("/register")
async def register_agent(agent: Agent, request: Request):
    """
    Register a new agent.

    Args:
        agent: Agent configuration

    Returns:
        Registration confirmation
    """
    tenant_id = get_tenant_id(request)

    if agent.name in agents_registry:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Agent '{agent.name}' already registered"
        )

    agents_registry[agent.name] = agent.model_dump()
    agents_registry[agent.name]["tenant_id"] = tenant_id

    return {
        "status": "registered",
        "agent": agent.name,
        "version": agent.version
    }


@router.put("/{name}/status")
async def update_agent_status(
    name: str,
    status: AgentStatus,
    request: Request
):
    """
    Update agent status.

    Args:
        name: Agent name/identifier
        status: New status

    Returns:
        Updated agent status
    """
    tenant_id = get_tenant_id(request)

    if name not in agents_registry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{name}' not found"
        )

    agents_registry[name]["status"] = status

    return {
        "agent": name,
        "status": status
    }