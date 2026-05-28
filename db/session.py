"""Database session utilities for AgentFlow."""

import uuid
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session, SessionTransaction
from sqlalchemy.pool import NullPool

from .models import Base


# Database URL - configure via environment variable
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/agentflow"

# Engine configuration
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Use NullPool for serverless/short-lived connections
    echo=False,
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db_session(tenant_id: uuid.UUID) -> Session:
    """
    Returns a database session with tenant context set for RLS.

    Args:
        tenant_id: The UUID of the tenant to scope the session to.

    Returns:
        SQLAlchemy Session with tenant context configured.
    """
    session = SessionLocal()
    # Set the tenant context for RLS policies
    session.execute(
        text("SELECT set_tenant_context(:tenant_id)"),
        {"tenant_id": str(tenant_id)}
    )
    return session


@contextmanager
def tenant_session(tenant_id: uuid.UUID) -> Generator[Session, None, None]:
    """
    Context manager for tenant-scoped database sessions.

    Args:
        tenant_id: The UUID of the tenant to scope the session to.

    Yields:
        SQLAlchemy Session with tenant context configured.
    """
    session = get_db_session(tenant_id)
    try:
        yield session
    finally:
        session.close()


def get_engine():
    """Returns the SQLAlchemy engine."""
    return engine


def get_session_factory():
    """Returns the session factory."""
    return SessionLocal


def init_db():
    """Initialize the database - creates all tables."""
    Base.metadata.create_all(bind=engine)


def close_db():
    """Close the database engine."""
    engine.dispose()