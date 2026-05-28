"""GDPR routes - consent management and data erasure."""
from fastapi import APIRouter, HTTPException, status, Request
from typing import List
from datetime import datetime
import uuid

from ..models import Consent, ConsentUpdate, ConsentStatus, ErasureRequest, ErasureResponse
from ..middleware.tenant import get_tenant_id

router = APIRouter(prefix="/gdpr", tags=["gdpr"])

# In-memory storage for demo
consents_store = {}
erasure_requests_store = {}


@router.get("/consents", response_model=List[Consent])
async def get_consents(request: Request):
    """
    Get all consent records for the tenant.

    Returns:
        List of consent records
    """
    tenant_id = get_tenant_id(request)

    tenant_consents = []
    for consent in consents_store.values():
        if consent.get("tenant_id") == tenant_id:
            tenant_consents.append(consent)

    return [Consent(**c) for c in tenant_consents]


@router.put("/consents", response_model=Consent)
async def update_consent(consent_update: ConsentUpdate, request: Request):
    """
    Update consent status for a specific purpose.

    Args:
        consent_update: Consent update request

    Returns:
        Updated consent record
    """
    tenant_id = get_tenant_id(request)
    purpose = consent_update.purpose

    # Find existing consent or create new
    storage_key = f"{tenant_id}:{purpose}"
    now = datetime.utcnow()

    if storage_key in consents_store:
        consent = consents_store[storage_key]
        consent["status"] = consent_update.status
        if consent_update.status == ConsentStatus.GRANTED:
            consent["granted_at"] = now
        elif consent_update.status == ConsentStatus.WITHDRAWN:
            consent["withdrawn_at"] = now
    else:
        consent_data = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "purpose": purpose,
            "status": consent_update.status,
            "granted_at": now if consent_update.status == ConsentStatus.GRANTED else None,
            "withdrawn_at": now if consent_update.status == ConsentStatus.WITHDRAWN else None,
            "version": "1.0"
        }
        consents_store[storage_key] = consent_data

    return Consent(**consents_store[storage_key])


@router.post("/erasure", response_model=ErasureResponse)
async def process_erasure_request(erasure_request: ErasureRequest, request: Request):
    """
    Process a GDPR erasure request.

    This endpoint handles the "right to be forgotten" by processing
    an erasure request for a specific user.

    Args:
        erasure_request: Erasure request with user_id

    Returns:
        Erasure request confirmation
    """
    tenant_id = get_tenant_id(request)

    # Create erasure request
    request_id = str(uuid.uuid4())
    now = datetime.utcnow()

    erasure_data = {
        "request_id": request_id,
        "tenant_id": tenant_id,
        "user_id": erasure_request.user_id,
        "reason": erasure_request.reason,
        "status": "processing",
        "created_at": now,
        "processed_at": None
    }

    erasure_requests_store[request_id] = erasure_data

    # In production, this would trigger an async workflow to:
    # 1. Delete user data from all services
    # 2. Anonymize or delete audit logs
    # 3. Process data from integrated systems
    # 4. Generate compliance report

    return ErasureResponse(
        request_id=request_id,
        status="accepted",
        processed_at=now
    )


@router.get("/erasure/{request_id}")
async def get_erasure_status(request_id: str, request: Request):
    """
    Get status of an erasure request.

    Args:
        request_id: Erasure request identifier

    Returns:
        Erasure request status
    """
    tenant_id = get_tenant_id(request)

    if request_id not in erasure_requests_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Erasure request {request_id} not found"
        )

    erasure = erasure_requests_store[request_id]
    if erasure["tenant_id"] != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Erasure request {request_id} not found"
        )

    return erasure