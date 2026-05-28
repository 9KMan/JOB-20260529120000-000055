"""
Session Manager - Redis-based conversation context storage.
"""
from typing import Optional
import json


class SessionManager:
    """Manages conversation sessions in Redis."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """
        Initialize session manager.

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self._client = None

    def _get_client(self):
        """Lazy-load Redis client."""
        if self._client is None:
            import redis
            self._client = redis.from_url(self.redis_url, decode_responses=True)
        return self._client

    def _session_key(self, tenant_id: str, session_id: str) -> str:
        """Generate Redis key for a session."""
        return f"session:{tenant_id}:{session_id}"

    def get_session(self, tenant_id: str, session_id: str) -> Optional[dict]:
        """
        Retrieve conversation context for a session.

        Args:
            tenant_id: Tenant identifier
            session_id: Session identifier

        Returns:
            Session context dict or None if not found
        """
        client = self._get_client()
        key = self._session_key(tenant_id, session_id)

        data = client.get(key)
        if data is None:
            return None

        return json.loads(data)

    def save_session(
        self,
        tenant_id: str,
        session_id: str,
        context: dict,
        ttl: int = 30 * 24 * 3600  # 30 days default
    ) -> None:
        """
        Save conversation context to Redis.

        Args:
            tenant_id: Tenant identifier
            session_id: Session identifier
            context: Session context dict
            ttl: Time to live in seconds (default 30 days)
        """
        client = self._get_client()
        key = self._session_key(tenant_id, session_id)

        # Serialize with JSON
        data = json.dumps(context, default=str)
        client.setex(key, ttl, data)

    def delete_tenant_sessions(self, tenant_id: str) -> int:
        """
        Delete all sessions for a tenant (GDPR right to erasure).

        Args:
            tenant_id: Tenant identifier

        Returns:
            Number of deleted sessions
        """
        client = self._get_client()

        # Find all session keys for this tenant
        pattern = f"session:{tenant_id}:*"

        # Use SCAN to avoid blocking
        cursor = 0
        deleted_count = 0

        while True:
            cursor, keys = client.scan(cursor, match=pattern, count=100)
            if keys:
                client.delete(*keys)
                deleted_count += len(keys)

            if cursor == 0:
                break

        return deleted_count

    def delete_session(self, tenant_id: str, session_id: str) -> bool:
        """
        Delete a specific session.

        Args:
            tenant_id: Tenant identifier
            session_id: Session identifier

        Returns:
            True if deleted, False if not found
        """
        client = self._get_client()
        key = self._session_key(tenant_id, session_id)

        return client.delete(key) > 0

    def extend_session(
        self,
        tenant_id: str,
        session_id: str,
        ttl: int = 30 * 24 * 3600
    ) -> bool:
        """
        Extend the TTL of a session.

        Args:
            tenant_id: Tenant identifier
            session_id: Session identifier
            ttl: New TTL in seconds

        Returns:
            True if TTL was extended, False if session not found
        """
        client = self._get_client()
        key = self._session_key(tenant_id, session_id)

        return client.expire(key, ttl)


# Singleton instance
_session_manager: Optional[SessionManager] = None


def get_session_manager(redis_url: str = "redis://localhost:6379/0") -> SessionManager:
    """Get or create the global SessionManager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager(redis_url)
    return _session_manager
