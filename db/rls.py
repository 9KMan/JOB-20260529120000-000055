"""Row-Level Security utilities for AgentFlow multi-tenant database."""

import uuid
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


def enforce_rls(session: Session, tenant_id: uuid.UUID) -> None:
    """
    Enforces Row-Level Security by setting the tenant context in the session.

    This must be called before any queries to ensure RLS policies are applied.

    Args:
        session: SQLAlchemy session to configure.
        tenant_id: The UUID of the tenant to enforce RLS for.
    """
    session.execute(
        text("SELECT set_tenant_context(:tenant_id)"),
        {"tenant_id": str(tenant_id)}
    )


def tenant_scope(query, tenant_id: uuid.UUID):
    """
    Applies tenant filtering to a SQLAlchemy query.

    This is an alternative to using RLS for cases where you need
    explicit tenant filtering in your queries.

    Args:
        query: SQLAlchemy query to apply tenant filter to.
        tenant_id: The UUID of the tenant to scope the query to.

    Returns:
        Query with tenant filter applied.
    """
    # Import here to avoid circular imports
    from .models import (
        Tenant, User, Workflow, AuditEvent,
        ApprovalQueue, TenantConsent, AgentMemory
    )

    # Get the model class from the query
    model = query.entity_zero.class_

    # Apply tenant_id filter if the model has a tenant_id column
    if hasattr(model, 'tenant_id'):
        return query.filter(model.tenant_id == tenant_id)

    return query


def get_current_tenant_id(session: Session) -> Optional[uuid.UUID]:
    """
    Gets the current tenant ID from the session context.

    Args:
        session: SQLAlchemy session to get tenant ID from.

    Returns:
        The current tenant UUID or None if not set.
    """
    result = session.execute(
        text("SELECT get_current_tenant_id()")
    )
    value = result.scalar()
    if value:
        return uuid.UUID(value)
    return None


def check_tenant_access(session: Session, resource_tenant_id: uuid.UUID) -> bool:
    """
    Checks if the current session has access to a resource belonging to a tenant.

    Args:
        session: SQLAlchemy session to check access for.
        resource_tenant_id: The tenant ID of the resource being accessed.

    Returns:
        True if access is allowed, False otherwise.
    """
    current_tenant = get_current_tenant_id(session)
    if current_tenant is None:
        return False
    return current_tenant == resource_tenant_id


def validate_tenant_id(tenant_id: Optional[uuid.UUID]) -> uuid.UUID:
    """
    Validates that a tenant_id is provided and is a valid UUID.

    Args:
        tenant_id: The tenant ID to validate.

    Returns:
        The validated tenant_id.

    Raises:
        ValueError: If tenant_id is None or invalid.
    """
    if tenant_id is None:
        raise ValueError("Tenant ID is required for this operation")
    if not isinstance(tenant_id, uuid.UUID):
        raise ValueError(f"Invalid tenant ID format: {tenant_id}")
    return tenant_id