"""
Memory Consolidation - Daily summarization of user interactions.
"""
from datetime import datetime, timedelta
from typing import Optional
import threading


class ConsolidationService:
    """Service for consolidating user memories into profiles."""

    def __init__(self, vector_store, session_store):
        """
        Initialize consolidation service.

        Args:
            vector_store: VectorStoreClient instance
            session_store: SessionManager instance
        """
        self.vector_store = vector_store
        self.session_store = session_store

    def consolidate_user_memory(self, tenant_id: str, user_id: str) -> dict:
        """
        Summarise recent interactions into user profile memory.

        Args:
            tenant_id: Tenant identifier
            user_id: User identifier

        Returns:
            Summary of consolidated memory
        """
        from datetime import datetime

        # Get recent sessions (last 7 days of activity)
        session_ids = self._get_recent_session_ids(tenant_id, user_id, days=7)

        if not session_ids:
            return {"status": "no_data", "user_id": user_id}

        # Collect all interactions from recent sessions
        interactions = []
        for session_id in session_ids:
            session = self.session_store.get_session(tenant_id, session_id)
            if session and "interactions" in session:
                interactions.extend(session["interactions"])

        if not interactions:
            return {"status": "no_interactions", "user_id": user_id}

        # Generate summary
        summary = self._generate_summary(interactions)

        # Write consolidated memory to vector store
        memory_id = self.vector_store.write_memory(
            tenant_id=tenant_id,
            user_id=user_id,
            memory_type="profile",
            content=summary,
            embedding=self.vector_store._generate_embedding(summary)
        )

        return {
            "status": "consolidated",
            "user_id": user_id,
            "memory_id": memory_id,
            "interactions_processed": len(interactions)
        }

    def _get_recent_session_ids(
        self, tenant_id: str, user_id: str, days: int = 7
    ) -> list[str]:
        """Get session IDs from recent days."""
        # In production, query session store by date range
        # Placeholder implementation
        return []

    def _generate_summary(self, interactions: list[dict]) -> str:
        """Generate a summary text from interactions."""
        if not interactions:
            return ""

        # Simple concatenation - in production use LLM summarization
        summary_parts = []
        for i, interaction in enumerate(interactions[-10:]):  # Last 10 interactions
            role = interaction.get("role", "unknown")
            content = interaction.get("content", "")[:100]
            summary_parts.append(f"{i+1}. {role}: {content}...")

        return " | ".join(summary_parts) if summary_parts else "No significant interactions"


class DailyJob:
    """Daily job for running memory consolidation."""

    def __init__(self, consolidation_service: ConsolidationService):
        """
        Initialize daily job.

        Args:
            consolidation_service: ConsolidationService instance
        """
        self.service = consolidation_service
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the daily consolidation job."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the daily consolidation job."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None

    def _run_loop(self) -> None:
        """Main loop - runs every 24 hours."""
        while self._running:
            self._run_consolidation()
            # Sleep for 24 hours (in production use proper scheduler)
            import time
            time.sleep(86400)  # 24 hours

    def _run_consolidation(self) -> None:
        """Run consolidation for all active tenants/users."""
        # In production: query for all active tenants and users
        # and run consolidation for each
        pass

    def run_now(self) -> None:
        """Run consolidation immediately (for testing/admin)."""
        self._run_consolidation()
