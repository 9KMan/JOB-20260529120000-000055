"""
SQLAlchemy models for AgentFlow memory and audit tables.
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, JSON, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ApprovalQueue(Base):
    """Stores pending and resolved approval requests."""
    __tablename__ = "approval_queue"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    workflow_id = Column(String(36), nullable=False, index=True)
    agent_name = Column(String(255), nullable=False)
    task_description = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    approver_id = Column(String(36), nullable=True)
    approver_note = Column(Text, nullable=True)

    __table_args__ = (
        Index("idx_approval_tenant_status", "tenant_id", "status"),
    )


class AuditEvents(Base):
    """Immutable audit log - INSERT only, no UPDATE/DELETE."""
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    actor_id = Column(String(36), nullable=False)
    action = Column(String(100), nullable=False, index=True)
    resource = Column(String(255), nullable=False, index=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Note: No updated_at - events are immutable
    # No deleted_at - records are never physically deleted


class TenantConsents(Base):
    """Stores GDPR consent records per tenant."""
    __tablename__ = "tenant_consents"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    consent_type = Column(String(100), nullable=False)
    granted = Column(Boolean, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_consent_tenant_type", "tenant_id", "consent_type", unique=True),
    )


class AgentMemory(Base):
    """Stores agent memory records in PostgreSQL (backup for Weaviate)."""
    __tablename__ = "agent_memory"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    memory_type = Column(String(50), nullable=False)  # interaction, profile, preference, etc.
    content = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_memory_tenant_user", "tenant_id", "user_id"),
        Index("idx_memory_tenant_type", "tenant_id", "memory_type"),
    )
