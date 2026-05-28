"""Authentication utilities for JWT verification."""
import os
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status

# Get JWT secret from environment
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"


def verify_jwt(token: str) -> str:
    """
    Verify JWT token and extract tenant_id.

    Args:
        token: JWT token string

    Returns:
        tenant_id extracted from token

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        tenant_id = payload.get("tenant_id")
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing tenant_id"
            )
        return tenant_id
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}"
        )


def create_test_token(tenant_id: str, user_id: Optional[str] = None) -> str:
    """
    Create a test JWT token (for development only).

    Args:
        tenant_id: Tenant identifier
        user_id: Optional user identifier

    Returns:
        JWT token string
    """
    import datetime
    payload = {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)