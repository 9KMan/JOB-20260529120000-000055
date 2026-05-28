"""SQLAlchemy models for AgentFlow database."""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, Text,
    UniqueConstraint, Index, JSON
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class Tenant(Base):
    """Tenant model representing an organization in the system."""

    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    region: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    users: Mapped[List["User"]] = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    workflows: Mapped[List["Workflow"]] = relationship("Workflow", back_populates="tenant", cascade="all, delete-orphan")
    audit_events: Mapped[List["AuditEvent"]] = relationship("AuditEvent", back_populates="tenant", cascade="all, delete-orphan")
    approval_queue: Mapped[List["ApprovalQueue"]] = relationship("ApprovalQueue", back_populates="tenant", cascade="all, delete-orphan")
    consents: Mapped[List["TenantConsent"]] = relationship("TenantConsent", back_populates="tenant", cascade="all, delete-orphan")
    agent_memory: Mapped[List["AgentMemory"]] = relationship("AgentMemory", back_populates="tenant", cascade="all, delete-orphan")


class User(Base):
    """User model belonging to a tenant."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")
    audit_events: Mapped[List["AuditEvent"]] = relationship("AuditEvent", back_populates="actor")
    approvals: Mapped[List["ApprovalQueue"]] = relationship("ApprovalQueue", back_populates="approver")
    memories: Mapped[List["AgentMemory"]] = relationship("AgentMemory", back_populates="user")

    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
        Index("idx_users_tenant_id", "tenant_id"),
        Index("idx_users_email", "email"),
        Index("idx_users_created_at", "created_at"),
    )


class Workflow(Base):
    """Workflow model representing an agent workflow definition."""

    __tablename__ = "workflows"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    definition: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="workflows")
    approval_queue: Mapped[List["ApprovalQueue"]] = relationship("ApprovalQueue", back_populates="workflow")

    __table_args__ = (
        Index("idx_workflows_tenant_id", "tenant_id"),
        Index("idx_workflows_created_at", "created_at"),
        Index("idx_workflows_status", "status"),
    )


class AuditEvent(Base):
    """Audit event model - immutable ledger of system events."""

    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    resource: Mapped[str] = mapped_column(String(255), nullable=False)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="audit_events")
    actor: Mapped[Optional["User"]] = relationship("User", back_populates="audit_events")

    __table_args__ = (
        Index("idx_audit_events_tenant_id", "tenant_id"),
        Index("idx_audit_events_actor_id", "actor_id"),
        Index("idx_audit_events_created_at", "created_at"),
    )


class ApprovalQueue(Base):
    """Approval queue for workflow tasks requiring human approval."""

    __tablename__ = "approval_queue"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    workflow_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=True)
    agent_name: Mapped[str] = mapped_column(String(255), nullable=False)
    task_description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    approver_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="approval_queue")
    workflow: Mapped[Optional["Workflow"]] = relationship("Workflow", back_populates="approval_queue")
    approver: Mapped[Optional["User"]] = relationship("User", back_populates="approvals")

    __table_args__ = (
        Index("idx_approval_queue_tenant_id", "tenant_id"),
        Index("idx_approval_queue_workflow_id", "workflow_id"),
        Index("idx_approval_queue_status", "status"),
        Index("idx_approval_queue_created_at", "created_at"),
    )


class TenantConsent(Base):
    """Tenant consent tracking for GDPR/data governance."""

    __tablename__ = "tenant_consents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    consent_type: Mapped[str] = mapped_column(String(255), nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    granted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="consents")

    __table_args__ = (
        UniqueConstraint("tenant_id", "consent_type", name="uq_tenant_consents_tenant_consent_type"),
        Index("idx_tenant_consents_tenant_id", "tenant_id"),
        Index("idx_tenant_consents_consent_type", "consent_type"),
    )


class AgentMemory(Base):
    """Agent memory for storing context and learned information."""

    __tablename__ = "agent_memory"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    memory_type: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    embedding: Mapped[Optional[List[float]]] = mapped_column(JSONB, nullable=True)  # Vector as JSON array
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="agent_memory")
    user: Mapped[Optional["User"]] = relationship("User", back_populates="memories")

    __table_args__ = (
        Index("idx_agent_memory_tenant_id", "tenant_id"),
        Index("idx_agent_memory_user_id", "user_id"),
        Index("idx_agent_memory_memory_type", "memory_type"),
        Index("idx_agent_memory_created_at", "created_at"),
    )