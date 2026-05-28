"""
Audit Ledger - Immutable audit log for all agent actions.
"""
from datetime import datetime
from typing import Optional, Any
import uuid


class AuditLedger:
    """Immutable audit log for tracking all agent operations."""

    def __init__(self, db_session_factory):
        """
        Initialize audit ledger.

        Args:
            db_session_factory: Database session factory callable
        """
        self.db_session_factory = db_session_factory

    def log_event(
        self,
        tenant_id: str,
        actor_id: str,
        action: str,
        resource: str,
        metadata: Optional[dict[str, Any]] = None
    ) -> str:
        """
        Create an immutable audit log record.

        Args:
            tenant_id: Tenant identifier
            actor_id: ID of the actor performing the action
            action: Action type (e.g., "approval_denied", "task_executed")
            resource: Resource identifier
            metadata: Additional metadata about the event

        Returns:
            event_id: Unique identifier for the audit event
        """
        from agentflow.db.memory_models import AuditEvents

        event_id = str(uuid.uuid4())

        session = self.db_session_factory()
        try:
            event = AuditEvents(
                id=event_id,
                tenant_id=tenant_id,
                actor_id=actor_id,
                action=action,
                resource=resource,
                metadata=metadata or {},
                created_at=datetime.utcnow()
            )
            session.add(event)
            session.commit()
            return event_id
        finally:
            session.close()

    def query_events(
        self,
        tenant_id: str,
        filters: Optional[dict] = None
    ) -> list[dict]:
        """
        Query audit events for a tenant.

        Args:
            tenant_id: Tenant identifier
            filters: Optional filters:
                - actor_id: Filter by actor
                - action: Filter by action type
                - resource: Filter by resource
                - start_date: Filter events after this date
                - end_date: Filter events before this date
                - limit: Max number of results (default 100)
                - offset: Pagination offset

        Returns:
            List of audit event records
        """
        from agentflow.db.memory_models import AuditEvents
        from sqlalchemy import and_

        filters = filters or {}

        session = self.db_session_factory()
        try:
            query = session.query(AuditEvents).filter(
                AuditEvents.tenant_id == tenant_id
            )

            if "actor_id" in filters:
                query = query.filter(AuditEvents.actor_id == filters["actor_id"])

            if "action" in filters:
                query = query.filter(AuditEvents.action == filters["action"])

            if "resource" in filters:
                query = query.filter(AuditEvents.resource == filters["resource"])

            if "start_date" in filters:
                query = query.filter(AuditEvents.created_at >= filters["start_date"])

            if "end_date" in filters:
                query = query.filter(AuditEvents.created_at <= filters["end_date"])

            limit = filters.get("limit", 100)
            offset = filters.get("offset", 0)

            events = query.order_by(
                AuditEvents.created_at.desc()
            ).limit(limit).offset(offset).all()

            return [self._record_to_dict(e) for e in events]
        finally:
            session.close()

    def _record_to_dict(self, record) -> dict:
        """Convert a model record to a dictionary."""
        return {
            "id": record.id,
            "tenant_id": record.tenant_id,
            "actor_id": record.actor_id,
            "action": record.action,
            "resource": record.resource,
            "metadata": record.metadata,
            "created_at": record.created_at.isoformat() if record.created_at else None
        }
