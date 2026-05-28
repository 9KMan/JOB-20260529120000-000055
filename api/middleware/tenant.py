"""Tenant context middleware - extracts tenant_id from JWT and injects into request state."""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from .auth import verify_jwt
from ..models import TenantContext


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware to extract and inject tenant context from JWT token."""

    async def dispatch(self, request: Request, call_next):
        # Skip tenant extraction for health checks and docs
        if request.url.path in ["/health", "/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)

        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            # Allow unauthenticated access for certain routes
            if request.url.path.startswith("/docs") or request.url.path.startswith("/openapi"):
                return await call_next(request)
            # For API routes, require authentication
            if request.url.path.startswith("/api"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing or invalid Authorization header"
                )
            return await call_next(request)

        token = auth_header.replace("Bearer ", "")

        try:
            tenant_id = verify_jwt(token)
            # Create tenant context and attach to request state
            request.state.tenant = TenantContext(
                tenant_id=tenant_id,
                user_id=None,
                roles=[]
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}"
            )

        return await call_next(request)


def get_tenant_id(request: Request) -> str:
    """
    Extract tenant_id from request state.

    Args:
        request: FastAPI request object

    Returns:
        tenant_id string

    Raises:
        HTTPException: If tenant context not found
    """
    if not hasattr(request.state, "tenant") or not request.state.tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant context not found"
        )
    return request.state.tenant.tenant_id