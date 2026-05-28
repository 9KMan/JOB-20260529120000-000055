"""Approval routes - manage approval workflows."""
from fastapi import APIRouter, HTTPException, status, Request
from typing import List, Optional
from datetime import datetime
import uuid

from ..models import Approval, ApprovalActionRequest, ApprovalStatus
from ..middleware.tenant import get_tenant_id

router = APIRouter(prefix="/approvals", tags=["approvals"])

# In-memory storage for demo
approvals_store = {}


@router.get("/", response_model=List[Approval])
async def list_pending_approvals(request: Request):
    """
    List all pending approvals for the tenant.

    Returns:
        List of pending approval requests
    """
    tenant_id = get_tenant_id(request)

    # Filter approvals by tenant and status
    tenant_approvals = []
    for approval in approvals_store.values():
        if approval.get("tenant_id") == tenant_id and approval["status"] == ApprovalStatus.PENDING:
            tenant_approvals.append(approval)

    return [Approval(**a) for a in tenant_approvals]


@router.post("/{approval_id}/approve")
async def approve_request(
    approval_id: str,
    action: ApprovalActionRequest,
    request: Request
):
    """
    Approve a pending request.

    Args:
        approval_id: Approval request identifier
        action: Optional note for the approval

    Returns:
        Updated approval record
    """
    tenant_id = get_tenant_id(request)
    storage_key = f"{tenant_id}:{approval_id}"

    if storage_key not in approvals_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval {approval_id} not found"
        )

    approval = approvals_store[storage_key]
    if approval["status"] != ApprovalStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Approval is not pending (current status: {approval['status']})"
        )

    # Update approval
    approval["status"] = ApprovalStatus.APPROVED
    approval["updated_at"] = datetime.utcnow()
    approval["note"] = action.note

    return {
        "id": approval_id,
        "status": "approved",
        "updated_at": approval["updated_at"],
        "note": approval["note"]
    }


@router.post("/{approval_id}/deny")
async def deny_request(
    approval_id: str,
    action: ApprovalActionRequest,
    request: Request
):
    """
    Deny a pending request.

    Args:
        approval_id: Approval request identifier
        action: Optional note for the denial

    Returns:
        Updated approval record
    """
    tenant_id = get_tenant_id(request)
    storage_key = f"{tenant_id}:{approval_id}"

    if storage_key not in approvals_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval {approval_id} not found"
        )

    approval = approvals_store[storage_key]
    if approval["status"] != ApprovalStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Approval is not pending (current status: {approval['status']})"
        )

    # Update approval
    approval["status"] = ApprovalStatus.DENIED
    approval["updated_at"] = datetime.utcnow()
    approval["note"] = action.note

    return {
        "id": approval_id,
        "status": "denied",
        "updated_at": approval["updated_at"],
        "note": approval["note"]
    }


@router.get("/{approval_id}", response_model=Approval)
async def get_approval(approval_id: str, request: Request):
    """
    Get a specific approval by ID.

    Args:
        approval_id: Approval request identifier

    Returns:
        Approval record
    """
    tenant_id = get_tenant_id(request)
    storage_key = f"{tenant_id}:{approval_id}"

    if storage_key not in approvals_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval {approval_id} not found"
        )

    return Approval(**approvals_store[storage_key])


# Helper function to create approvals (for testing)
def create_approval(tenant_id: str, approval_type: str, requester_id: str, requester_name: str) -> Approval:
    """Create a new approval request."""
    approval_id = str(uuid.uuid4())
    now = datetime.utcnow()

    approval_data = {
        "id": approval_id,
        "tenant_id": tenant_id,
        "type": approval_type,
        "status": ApprovalStatus.PENDING,
        "requester_id": requester_id,
        "requester_name": requester_name,
        "created_at": now,
        "updated_at": None,
        "note": None
    }

    storage_key = f"{tenant_id}:{approval_id}"
    approvals_store[storage_key] = approval_data

    return Approval(**approval_data)