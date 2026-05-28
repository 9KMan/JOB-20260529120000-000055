"""Pydantic models for request/response schemas."""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Chat message model."""
    role: MessageRole
    content: str
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    """Request model for sending chat messages."""
    message: str = Field(..., min_length=1)
    thread_id: Optional[str] = None
    agent_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for chat."""
    thread_id: str
    message: str
    agent: Optional[str] = None


class ThreadResponse(BaseModel):
    """Response model for thread messages."""
    thread_id: str
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: datetime


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"


class Approval(BaseModel):
    """Approval model."""
    id: str
    type: str
    status: ApprovalStatus
    requester_id: str
    requester_name: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    note: Optional[str] = None


class ApprovalActionRequest(BaseModel):
    """Request model for approval actions."""
    note: Optional[str] = None


class AuditEvent(BaseModel):
    """Audit event model."""
    id: str
    timestamp: datetime
    event_type: str
    actor_id: str
    actor_name: str
    resource_type: str
    resource_id: Optional[str] = None
    action: str
    details: Optional[dict] = None
    ip_address: Optional[str] = None


class AuditQuery(BaseModel):
    """Query parameters for audit events."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    event_type: Optional[str] = None
    actor_id: Optional[str] = None
    resource_type: Optional[str] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)


class ConsentStatus(str, Enum):
    GRANTED = "granted"
    DENIED = "denied"
    WITHDRAWN = "withdrawn"


class Consent(BaseModel):
    """Consent record model."""
    id: str
    purpose: str
    status: ConsentStatus
    granted_at: Optional[datetime] = None
    withdrawn_at: Optional[datetime] = None
    version: str


class ConsentUpdate(BaseModel):
    """Request model for updating consent."""
    purpose: str
    status: ConsentStatus


class ErasureRequest(BaseModel):
    """Request model for GDPR erasure."""
    user_id: str
    reason: Optional[str] = None


class ErasureResponse(BaseModel):
    """Response model for erasure request."""
    request_id: str
    status: str
    processed_at: datetime


class AgentStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAINING = "draining"


class Agent(BaseModel):
    """Agent model."""
    name: str
    description: str
    version: str
    status: AgentStatus
    capabilities: List[str]
    endpoint: Optional[str] = None


class TenantContext(BaseModel):
    """Tenant context extracted from JWT."""
    tenant_id: str
    user_id: Optional[str] = None
    roles: List[str] = Field(default_factory=list)