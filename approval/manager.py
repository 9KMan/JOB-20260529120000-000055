"""
Approval Gate Manager - Handles approval workflows for agent tasks.
"""
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class ApprovalStatus(str, Enum):
    """Approval request status."""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    TIMEOUT = "timeout"


class ApprovalManager:
    """Manages approval requests and workflows."""

    def __init__(self, db_session_factory):
        """
        Initialize approval manager.

        Args:
            db_session_factory: Database session factory callable
        """
        self.db_session_factory = db_session_factory

    def create_approval_request(
        self,
        tenant_id: str,
        workflow_id: str,
        agent_name: str,
        task_description: str
    ) -> str:
        """
        Create a new approval request.

        Args:
            tenant_id: Tenant identifier
            workflow_id: Associated workflow ID
            agent_name: Name of the agent requesting approval
            task_description: Description of the task needing approval

        Returns:
            approval_id: Unique identifier for the approval request
        """
        from agentflow.db.memory_models import ApprovalQueue

        approval_id = str(uuid.uuid4())

        session = self.db_session_factory()
        try:
            request = ApprovalQueue(
                id=approval_id,
                tenant_id=tenant_id,
                workflow_id=workflow_id,
                agent_name=agent_name,
                task_description=task_description,
                status=ApprovalStatus.PENDING.value,
                created_at=datetime.utcnow()
            )
            session.add(request)
            session.commit()
            return approval_id
        finally:
            session.close()

    def get_pending_approvals(self, tenant_id: str) -> list[dict]:
        """
        Get all pending approvals for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            List of pending approval records
        """
        from agentflow.db.memory_models import ApprovalQueue

        session = self.db_session_factory()
        try:
            records = session.query(ApprovalQueue).filter(
                ApprovalQueue.tenant_id == tenant_id,
                ApprovalQueue.status == ApprovalStatus.PENDING.value
            ).order_by(ApprovalQueue.created_at.desc()).all()

            return [self._record_to_dict(r) for r in records]
        finally:
            session.close()

    def approve(
        self,
        approval_id: str,
        approver_id: str,
        note: Optional[str] = None
    ) -> dict:
        """
        Approve a pending request and resume execution.

        Args:
            approval_id: Approval request ID
            approver_id: ID of the approver
            note: Optional approval note

        Returns:
            Result dict with status and metadata
        """
        from agentflow.db.memory_models import ApprovalQueue

        session = self.db_session_factory()
        try:
            request = session.query(ApprovalQueue).filter(
                ApprovalQueue.id == approval_id
            ).first()

            if not request:
                return {"status": "error", "message": "Approval request not found"}

            if request.status != ApprovalStatus.PENDING.value:
                return {"status": "error", "message": f"Request is not pending, current status: {request.status}"}

            request.status = ApprovalStatus.APPROVED.value
            request.approver_id = approver_id
            request.approver_note = note
            request.resolved_at = datetime.utcnow()

            session.commit()

            return {
                "status": "approved",
                "approval_id": approval_id,
                "approver_id": approver_id,
                "action": "resume_execution"
            }
        finally:
            session.close()

    def deny(
        self,
        approval_id: str,
        approver_id: str,
        note: Optional[str] = None
    ) -> dict:
        """
        Deny a request and log the denial with alternative suggestion.

        Args:
            approval_id: Approval request ID
            approver_id: ID of the approver
            note: Optional denial note with reason

        Returns:
            Result dict with denial info and alternative suggestion
        """
        from agentflow.db.memory_models import ApprovalQueue

        session = self.db_session_factory()
        try:
            request = session.query(ApprovalQueue).filter(
                ApprovalQueue.id == approval_id
            ).first()

            if not request:
                return {"status": "error", "message": "Approval request not found"}

            request.status = ApprovalStatus.DENIED.value
            request.approver_id = approver_id
            request.approver_note = note
            request.resolved_at = datetime.utcnow()

            session.commit()

            # Log the denial in audit ledger
            from agentflow.audit.ledger import AuditLedger
            ledger = AuditLedger(self.db_session_factory)
            ledger.log_event(
                tenant_id=request.tenant_id,
                actor_id=approver_id,
                action="approval_denied",
                resource=f"approval:{approval_id}",
                metadata={
                    "workflow_id": request.workflow_id,
                    "agent_name": request.agent_name,
                    "task_description": request.task_description,
                    "note": note
                }
            )

            # Generate alternative suggestion based on context
            alternative = self._generate_alternative(request)

            return {
                "status": "denied",
                "approval_id": approval_id,
                "approver_id": approver_id,
                "reason": note or "Request denied",
                "alternative_suggestion": alternative
            }
        finally:
            session.close()

    def get_approval_status(self, approval_id: str) -> Optional[dict]:
        """
        Get the current status of an approval request.

        Args:
            approval_id: Approval request ID

        Returns:
            Status dict or None if not found
        """
        from agentflow.db.memory_models import ApprovalQueue

        session = self.db_session_factory()
        try:
            request = session.query(ApprovalQueue).filter(
                ApprovalQueue.id == approval_id
            ).first()

            if not request:
                return None

            return self._record_to_dict(request)
        finally:
            session.close()

    def _record_to_dict(self, record) -> dict:
        """Convert a model record to a dictionary."""
        return {
            "id": record.id,
            "tenant_id": record.tenant_id,
            "workflow_id": record.workflow_id,
            "agent_name": record.agent_name,
            "task_description": record.task_description,
            "status": record.status,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "resolved_at": record.resolved_at.isoformat() if record.resolved_at else None,
            "approver_id": record.approver_id,
            "approver_note": record.approver_note
        }

    def _generate_alternative(self, request) -> str:
        """Generate an alternative suggestion for a denied request."""
        # Placeholder - in production, could use LLM to generate suggestions
        return (
            f"Consider breaking down the task '{request.task_description}' into "
            f"smaller steps that can be approved individually, or modify the "
            f"parameters to reduce risk."
        )

    def mark_timeout(self, approval_id: str) -> dict:
        """
        Mark an approval request as timed out.

        Args:
            approval_id: Approval request ID

        Returns:
            Result dict
        """
        from agentflow.db.memory_models import ApprovalQueue

        session = self.db_session_factory()
        try:
            request = session.query(ApprovalQueue).filter(
                ApprovalQueue.id == approval_id
            ).first()

            if not request:
                return {"status": "error", "message": "Approval request not found"}

            if request.status != ApprovalStatus.PENDING.value:
                return {"status": "error", "message": f"Request is not pending: {request.status}"}

            request.status = ApprovalStatus.TIMEOUT.value
            request.resolved_at = datetime.utcnow()

            session.commit()

            return {
                "status": "timeout",
                "approval_id": approval_id
            }
        finally:
            session.close()
