"""Audit routes - query and filter audit events."""
from fastapi import APIRouter, HTTPException, Request, Query
from typing import Optional, List
from datetime import datetime, timedelta

from ..models import AuditEvent, AuditQuery
from ..middleware.tenant import get_tenant_id

router = APIRouter(prefix="/audit", tags=["audit"])

# In-memory storage for demo
audit_events_store = []


@router.get("/", response_model=List[AuditEvent])
async def query_audit_events(
    request: Request,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    event_type: Optional[str] = Query(None),
    actor_id: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    Query audit events with filters.

    Args:
        start_date: Filter events after this date
        end_date: Filter events before this date
        event_type: Filter by event type
        actor_id: Filter by actor identifier
        resource_type: Filter by resource type
        limit: Maximum number of results (default 100, max 1000)
        offset: Offset for pagination

    Returns:
        List of matching audit events
    """
    tenant_id = get_tenant_id(request)

    # Filter events by tenant and criteria
    filtered_events = []
    for event in audit_events_store:
        if event.get("tenant_id") != tenant_id:
            continue

        # Apply filters
        if start_date and event["timestamp"] < start_date:
            continue
        if end_date and event["timestamp"] > end_date:
            continue
        if event_type and event.get("event_type") != event_type:
            continue
        if actor_id and event.get("actor_id") != actor_id:
            continue
        if resource_type and event.get("resource_type") != resource_type:
            continue

        filtered_events.append(event)

    # Apply pagination
    return filtered_events[offset:offset + limit]


@router.get("/{event_id}", response_model=AuditEvent)
async def get_audit_event(event_id: str, request: Request):
    """
    Get a specific audit event by ID.

    Args:
        event_id: Audit event identifier

    Returns:
        Audit event record
    """
    tenant_id = get_tenant_id(request)

    for event in audit_events_store:
        if event.get("tenant_id") == tenant_id and event["id"] == event_id:
            return AuditEvent(**event)

    raise HTTPException(status_code=404, detail=f"Audit event {event_id} not found")


@router.post("/")
async def create_audit_event(
    event_type: str,
    actor_id: str,
    actor_name: str,
    resource_type: str,
    action: str,
    request: Request,
    resource_id: Optional[str] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None
):
    """
    Create a new audit event (internal use).

    Args:
        event_type: Type of event
        actor_id: Actor identifier
        actor_name: Actor display name
        resource_type: Type of resource
        action: Action performed
        resource_id: Optional resource identifier
        details: Optional additional details
        ip_address: Optional IP address

    Returns:
        Created audit event
    """
    tenant_id = get_tenant_id(request)

    event = AuditEvent(
        id=f"audit_{datetime.utcnow().timestamp()}",
        timestamp=datetime.utcnow(),
        event_type=event_type,
        actor_id=actor_id,
        actor_name=actor_name,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        details=details,
        ip_address=ip_address
    )

    event_dict = event.model_dump()
    event_dict["tenant_id"] = tenant_id
    audit_events_store.append(event_dict)

    return event


# Helper function to log events
def log_audit_event(
    tenant_id: str,
    event_type: str,
    actor_id: str,
    actor_name: str,
    resource_type: str,
    action: str,
    resource_id: Optional[str] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None
):
    """Log an audit event (for internal use by other components)."""
    event = AuditEvent(
        id=f"audit_{datetime.utcnow().timestamp()}",
        timestamp=datetime.utcnow(),
        event_type=event_type,
        actor_id=actor_id,
        actor_name=actor_name,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        details=details,
        ip_address=ip_address
    )

    event_dict = event.model_dump()
    event_dict["tenant_id"] = tenant_id
    audit_events_store.append(event_dict)

    return event