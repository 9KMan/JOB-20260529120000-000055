"""
Tests for Approval Flow.
"""
import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta
import threading
import time


class TestApprovalFlow:
    """Test cases for approval flow functionality."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session factory."""
        def make_session():
            mock_session = MagicMock()
            mock_session.query.return_value.filter.return_value.first.return_value = None
            mock_session.query.return_value.filter.return_value.all.return_value = []
            return mock_session
        return make_session

    @pytest.fixture
    def mock_vector_store(self):
        """Create a mock vector store client."""
        mock = Mock()
        mock.write_memory.return_value = "test_memory_id"
        mock.delete_tenant_memories.return_value = 0
        mock._generate_embedding.return_value = [0.0] * 384
        return mock

    @pytest.fixture
    def mock_session_store(self):
        """Create a mock session manager."""
        mock = Mock()
        mock.get_session.return_value = None
        mock.delete_tenant_sessions.return_value = 0
        return mock

    def test_approval_gate_creates_pending_request(self, mock_db_session):
        """Test that creating an approval request results in a pending status."""
        from agentflow.approval.manager import ApprovalManager, ApprovalStatus

        # Setup mock to return None initially (no existing record)
        mock_record = Mock()
        mock_record.id = "test_approval_id"
        mock_record.tenant_id = "tenant_1"
        mock_record.workflow_id = "workflow_1"
        mock_record.agent_name = "TestAgent"
        mock_record.task_description = "Test task description"
        mock_record.status = ApprovalStatus.PENDING.value
        mock_record.created_at = datetime.utcnow()

        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_record
        mock_session.query.return_value.filter.return_value.all.return_value = [mock_record]
        mock_session_factory = Mock(return_value=mock_session)

        manager = ApprovalManager(mock_session_factory)

        # Create approval request
        approval_id = manager.create_approval_request(
            tenant_id="tenant_1",
            workflow_id="workflow_1",
            agent_name="TestAgent",
            task_description="Test task description"
        )

        # Verify it was created
        assert approval_id is not None
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_approve_resumes_execution(self, mock_db_session):
        """Test that approving a request returns status to resume execution."""
        from agentflow.approval.manager import ApprovalManager, ApprovalStatus

        # Setup pending request
        pending_record = Mock()
        pending_record.id = "approval_123"
        pending_record.tenant_id = "tenant_1"
        pending_record.workflow_id = "workflow_1"
        pending_record.agent_name = "TestAgent"
        pending_record.task_description = "Deploy application"
        pending_record.status = ApprovalStatus.PENDING.value
        pending_record.created_at = datetime.utcnow()
        pending_record.resolved_at = None
        pending_record.approver_id = None
        pending_record.approver_note = None

        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = pending_record
        mock_session_factory = Mock(return_value=mock_session)

        manager = ApprovalManager(mock_session_factory)

        # Approve the request
        result = manager.approve(
            approval_id="approval_123",
            approver_id="approver_1",
            note="Approved for production deployment"
        )

        # Verify result
        assert result["status"] == "approved"
        assert result["action"] == "resume_execution"
        assert pending_record.status == ApprovalStatus.APPROVED.value
        assert pending_record.approver_id == "approver_1"
        assert pending_record.approver_note == "Approved for production deployment"

    def test_deny_logs_and_returns_alternative(self, mock_db_session):
        """Test that denying a request logs the denial and returns alternative suggestion."""
        from agentflow.approval.manager import ApprovalManager, ApprovalStatus

        # Setup pending request
        pending_record = Mock()
        pending_record.id = "approval_456"
        pending_record.tenant_id = "tenant_1"
        pending_record.workflow_id = "workflow_1"
        pending_record.agent_name = "TestAgent"
        pending_record.task_description = "Delete production database"
        pending_record.status = ApprovalStatus.PENDING.value
        pending_record.created_at = datetime.utcnow()
        pending_record.resolved_at = None
        pending_record.approver_id = None
        pending_record.approver_note = None

        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = pending_record
        mock_session_factory = Mock(return_value=mock_session)

        manager = ApprovalManager(mock_session_factory)

        # Deny the request
        result = manager.deny(
            approval_id="approval_456",
            approver_id="approver_1",
            note="Too risky - requires additional review"
        )

        # Verify denial was recorded
        assert result["status"] == "denied"
        assert result["reason"] == "Too risky - requires additional review"
        assert pending_record.status == ApprovalStatus.DENIED.value

        # Verify alternative suggestion was returned
        assert "alternative_suggestion" in result
        assert len(result["alternative_suggestion"]) > 0

    def test_timeout_auto_deny(self, mock_db_session):
        """Test that pending approvals timeout and are auto-denied."""
        from agentflow.approval.manager import ApprovalManager, ApprovalStatus

        # Create a manager that tracks timeouts
        timeout_manager = ApprovalManager(mock_db_session)

        # Setup expired pending request (created 25 hours ago, timeout is 24 hours)
        expired_record = Mock()
        expired_record.id = "approval_789"
        expired_record.tenant_id = "tenant_1"
        expired_record.workflow_id = "workflow_1"
        expired_record.agent_name = "TestAgent"
        expired_record.task_description = "Automated task"
        expired_record.status = ApprovalStatus.PENDING.value
        expired_record.created_at = datetime.utcnow() - timedelta(hours=25)
        expired_record.resolved_at = None
        expired_record.approver_id = None
        expired_record.approver_note = None

        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = expired_record
        mock_session_factory = Mock(return_value=mock_session)

        manager = ApprovalManager(mock_session_factory)

        # Check if expired
        def is_expired(created_at, timeout_hours=24):
            return datetime.utcnow() - created_at > timedelta(hours=timeout_hours)

        if is_expired(expired_record.created_at):
            # Mark as timeout
            result = manager.mark_timeout("approval_789")
            assert result["status"] == "timeout"
            assert expired_record.status == ApprovalStatus.TIMEOUT.value

            # Verify no approver was set (system auto-denied)
            assert expired_record.approver_id is None

    def test_get_pending_approvals(self, mock_db_session):
        """Test retrieving all pending approvals for a tenant."""
        from agentflow.approval.manager import ApprovalManager

        # Setup multiple pending requests
        pending_records = []
        for i in range(3):
            mock_record = Mock()
            mock_record.id = f"approval_{i}"
            mock_record.tenant_id = "tenant_1"
            mock_record.workflow_id = f"workflow_{i}"
            mock_record.agent_name = "TestAgent"
            mock_record.task_description = f"Task {i}"
            mock_record.status = "pending"
            mock_record.created_at = datetime.utcnow() - timedelta(hours=i)
            mock_record.resolved_at = None
            mock_record.approver_id = None
            mock_record.approver_note = None
            pending_records.append(mock_record)

        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.all.return_value = pending_records
        mock_session_factory = Mock(return_value=mock_session)

        manager = ApprovalManager(mock_session_factory)

        # Get pending approvals
        pending = manager.get_pending_approvals("tenant_1")

        assert len(pending) == 3
        # Verify sorted by created_at desc
        assert pending[0]["id"] == "approval_0"  # Most recent first

    def test_approval_status_not_found(self, mock_db_session):
        """Test getting status of non-existent approval."""
        from agentflow.approval.manager import ApprovalManager

        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_session_factory = Mock(return_value=mock_session)

        manager = ApprovalManager(mock_session_factory)

        # Get non-existent approval
        status = manager.get_approval_status("nonexistent_id")

        assert status is None

    def test_double_approve_fails(self, mock_db_session):
        """Test that approving an already approved request fails."""
        from agentflow.approval.manager import ApprovalManager, ApprovalStatus

        # Setup already approved request
        approved_record = Mock()
        approved_record.id = "approval_double"
        approved_record.tenant_id = "tenant_1"
        approved_record.workflow_id = "workflow_1"
        approved_record.agent_name = "TestAgent"
        approved_record.task_description = "Task"
        approved_record.status = ApprovalStatus.APPROVED.value
        approved_record.created_at = datetime.utcnow()
        approved_record.resolved_at = datetime.utcnow()
        approved_record.approver_id = "first_approver"
        approved_record.approver_note = None

        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = approved_record
        mock_session_factory = Mock(return_value=mock_session)

        manager = ApprovalManager(mock_session_factory)

        # Try to approve again
        result = manager.approve(
            approval_id="approval_double",
            approver_id="second_approver"
        )

        assert result["status"] == "error"
        assert "not pending" in result["message"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
