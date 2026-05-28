"""
Vector Store Client - Weaviate integration for memory storage.
"""
from typing import Optional
import uuid


class VectorStoreClient:
    """Client for Weaviate vector store operations."""

    def __init__(self, url: str, api_key: Optional[str] = None):
        """
        Initialize Weaviate client.

        Args:
            url: Weaviate instance URL
            api_key: Optional API key for authentication
        """
        self.url = url
        self.api_key = api_key
        self._client = None

    def _get_client(self):
        """Lazy-load Weaviate client."""
        if self._client is None:
            import weaviate
            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            self._client = weaviate.Client(self.url, headers=headers)
        return self._client

    def tenant_scoped_search(
        self, tenant_id: str, query: str, top_k: int = 5
    ) -> list[dict]:
        """
        Search memories filtered by tenant.

        Args:
            tenant_id: Tenant identifier
            query: Search query text
            top_k: Number of results to return

        Returns:
            List of matching memory records with scores
        """
        client = self._get_client()

        # Generate embedding for query
        embedding = self._generate_embedding(query)

        # Search with tenant filter
        where_filter = {
            "operator": "Equal",
            "path": ["tenant_id"],
            "valueString": tenant_id
        }

        result = client.search(
            collection_name="AgentMemory",
            query_vector=embedding,
            limit=top_k,
            where=where_filter
        )

        return [
            {"id": hit.id, "content": hit.payload, "score": hit.score}
            for hit in result.hits
        ]

    def write_memory(
        self,
        tenant_id: str,
        user_id: str,
        memory_type: str,
        content: str,
        embedding: list[float]
    ) -> str:
        """
        Write a memory record to the vector store.

        Args:
            tenant_id: Tenant identifier
            user_id: User identifier
            memory_type: Type of memory (interaction, profile, preference, etc.)
            content: Memory content text
            embedding: Vector embedding of the content

        Returns:
            ID of created memory record
        """
        client = self._get_client()

        memory_id = str(uuid.uuid4())

        client.data_object.create(
            class_name="AgentMemory",
            uuid=memory_id,
            data_object={
                "tenant_id": tenant_id,
                "user_id": user_id,
                "memory_type": memory_type,
                "content": content,
                "embedding": embedding
            }
        )

        return memory_id

    def delete_tenant_memories(self, tenant_id: str) -> int:
        """
        Delete all memories for a tenant (GDPR right to erasure).

        Args:
            tenant_id: Tenant identifier

        Returns:
            Number of deleted memory records
        """
        client = self._get_client()

        where_filter = {
            "operator": "Equal",
            "path": ["tenant_id"],
            "valueString": tenant_id
        }

        # Get all matching IDs first
        result = client.query.get(
            collection_name="AgentMemory",
            properties=["id"]
        ).with_where(where_filter).do()

        ids_to_delete = [obj["id"] for obj in result.get("objects", [])]

        # Delete all records
        for obj_id in ids_to_delete:
            client.data_object.delete(obj_id)

        return len(ids_to_delete)

    def _generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding using bge-m3 or equivalent model.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        # Placeholder for bge-m3 embedding model integration
        # In production, use: from sentence_transformers import SentenceTransformer
        # model = SentenceTransformer('BAAI/bge-m3')
        # return model.encode(text).tolist()
        import hashlib
        # Deterministic fake embedding for testing
        embedding = [0.0] * 384
        for i, char in enumerate(text):
            embedding[i % 384] += hashlib.sha256(char.encode()).digest()[0] / 255.0
        return embedding


# Singleton instance
_client: Optional[VectorStoreClient] = None


def get_vector_store(url: str, api_key: Optional[str] = None) -> VectorStoreClient:
    """Get or create the global VectorStoreClient instance."""
    global _client
    if _client is None:
        _client = VectorStoreClient(url, api_key)
    return _client
