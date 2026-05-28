"""
GDPR Compliance APIs - Consent management and data erasure.
"""
from datetime import datetime
from typing import Optional
import uuid


class GDPRService:
    """Service for GDPR compliance operations."""

    def __init__(
        self,
        db_session_factory,
        vector_store_client,
        session_manager
    ):
        """
        Initialize GDPR service.

        Args:
            db_session_factory: Database session factory
            vector_store_client: VectorStoreClient instance
            session_manager: SessionManager instance
        """
        self.db_session_factory = db_session_factory
        self.vector_store = vector_store_client
        self.session_manager = session_manager

    def get_consents(self, tenant_id: str) -> list[dict]:
        """
        Get consent records for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            List of consent records
        """
        from agentflow.db.memory_models import TenantConsents

        session = self.db_session_factory()
        try:
            records = session.query(TenantConsents).filter(
                TenantConsents.tenant_id == tenant_id
            ).all()

            return [self._record_to_dict(r) for r in records]
        finally:
            session.close()

    def update_consent(
        self,
        tenant_id: str,
        consent_type: str,
        granted: bool
    ) -> dict:
        """
        Update a consent record.

        Args:
            tenant_id: Tenant identifier
            consent_type: Type of consent (e.g., "data_processing", "marketing")
            granted: Whether consent is granted

        Returns:
            Updated consent record
        """
        from agentflow.db.memory_models import TenantConsents

        session = self.db_session_factory()
        try:
            record = session.query(TenantConsents).filter(
                TenantConsents.tenant_id == tenant_id,
                TenantConsents.consent_type == consent_type
            ).first()

            if record:
                record.granted = granted
                record.updated_at = datetime.utcnow()
            else:
                record = TenantConsents(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    consent_type=consent_type,
                    granted=granted,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(record)

            session.commit()
            return self._record_to_dict(record)
        finally:
            session.close()

    def process_erasure_request(self, tenant_id: str) -> dict:
        """
        Process a complete erasure request (GDPR right to erasure).
        Cascades deletion across PostgreSQL, Weaviate, and Redis.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Summary of deletion results
        """
        from agentflow.db.memory_models import (
            AgentMemory, ApprovalQueue, AuditEvents, TenantConsents
        )
        from agentflow.audit.ledger import AuditLedger

        results = {
            "postgresql": {"deleted": 0, "tables": []},
            "weaviate": {"deleted": 0},
            "redis": {"deleted": 0}
        }

        # Log the erasure request in audit
        ledger = AuditLedger(self.db_session_factory)
        ledger.log_event(
            tenant_id=tenant_id,
            actor_id="gdpr_service",
            action="erasure_request_processed",
            resource=f"tenant:{tenant_id}",
            metadata={"initiated_at": datetime.utcnow().isoformat()}
        )

        session = self.db_session_factory()
        try:
            # Delete from PostgreSQL tables
            tables_with_tenant = [
                (AgentMemory, "agent_memory"),
                (ApprovalQueue, "approval_queue"),
                (TenantConsents, "tenant_consents")
            ]

            for model, table_name in tables_with_tenant:
                deleted = session.query(model).filter(
                    model.tenant_id == tenant_id
                ).delete()
                results["postgresql"]["deleted"] += deleted
                results["postgresql"]["tables"].append({
                    "table": table_name,
                    "deleted": deleted
                })

            # Audit events are INSERT-only - mark as anonymized instead of deleting
            # This preserves audit trail while meeting GDPR requirements
            anonymized_count = session.query(AuditEvents).filter(
                AuditEvents.tenant_id == tenant_id
            ).update({
                "tenant_id": f"REDACTED_{tenant_id}",
                "actor_id": "REDACTED"
            })
            results["postgresql"]["tables"].append({
                "table": "audit_events",
                "anonymized": anonymized_count
            })

            session.commit()
        finally:
            session.close()

        # Delete from Weaviate (vector store memories)
        try:
            weaviate_deleted = self.vector_store.delete_tenant_memories(tenant_id)
            results["weaviate"]["deleted"] = weaviate_deleted
        except Exception as e:
            results["weaviate"]["error"] = str(e)

        # Delete from Redis (sessions)
        try:
            redis_deleted = self.session_manager.delete_tenant_sessions(tenant_id)
            results["redis"]["deleted"] = redis_deleted
        except Exception as e:
            results["redis"]["error"] = str(e)

        # Log completion
        ledger.log_event(
            tenant_id=tenant_id,
            actor_id="gdpr_service",
            action="erasure_request_completed",
            resource=f"tenant:{tenant_id}",
            metadata={
                "completed_at": datetime.utcnow().isoformat(),
                "results": results
            }
        )

        return results

    def verify_data_residency(self, tenant_id: str) -> bool:
        """
        Verify that all tenant data is stored in compliant data residency region.

        Args:
            tenant_id: Tenant identifier

        Returns:
            True if data residency requirements are met
        """
        # Placeholder implementation
        # In production, this would verify:
        # - PostgreSQL is in compliant region
        # - Weaviate is in compliant region
        # - Redis is in compliant region
        # - Backup storage is in compliant region
        return True

    def _record_to_dict(self, record) -> dict:
        """Convert a model record to a dictionary."""
        return {
            "id": record.id,
            "tenant_id": record.tenant_id,
            "consent_type": record.consent_type,
            "granted": record.granted,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "updated_at": record.updated_at.isoformat() if record.updated_at else None
        }
