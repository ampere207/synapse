"""Embedding and vector database service for semantic memory"""
import hashlib
import json
from typing import List, Dict, Any, Optional, Tuple
import numpy as np


class EmbeddingService:
    """Service for generating and managing embeddings"""

    # Placeholder embedding dimension (would be 768+ with real embeddings)
    EMBEDDING_DIM = 768

    @staticmethod
    def hash_to_embedding(text: str, dim: int = 768) -> List[float]:
        """
        Generate a deterministic pseudo-embedding from text hash.
        In production, this would call a real embedding model (Sentence Transformers, etc).
        """
        # Create a consistent hash from text
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Seed RNG with hash for reproducibility
        seed = int.from_bytes(hash_bytes[:8], byteorder='big')
        rng = np.random.RandomState(seed)
        
        # Generate pseudo-random embedding
        embedding = rng.randn(dim).astype(np.float32)
        
        # Normalize to unit vector
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding.tolist()

    @staticmethod
    def cosine_similarity(emb1: List[float], emb2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        a = np.array(emb1)
        b = np.array(emb2)
        
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(dot_product / (norm_a * norm_b))

    @staticmethod
    def embed_text(text: str, model: Optional[str] = None) -> List[float]:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed
            model: Model to use (placeholder for future integration)
            
        Returns:
            Embedding vector
        """
        # TODO: In production, integrate with:
        # - Sentence Transformers (sentence-transformers/all-MiniLM-L6-v2)
        # - OpenAI embeddings
        # - Google embeddings
        # - Hugging Face inference API
        
        return EmbeddingService.hash_to_embedding(text, dim=EmbeddingService.EMBEDDING_DIM)

    @staticmethod
    def embed_batch(texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        embeddings = []
        for text in texts:
            embeddings.append(EmbeddingService.embed_text(text))
        return embeddings


class QdrantMemoryService:
    """Service for managing semantic memory in vector database (Qdrant)"""

    def __init__(self, qdrant_host: str = "qdrant", qdrant_port: int = 6333, api_key: Optional[str] = None):
        """Initialize Qdrant service (HTTP client).

        If `qdrant-client` is not installed the service will continue to work
        with in-memory stubs (useful for local dev without Qdrant).
        """
        self.host = qdrant_host
        self.port = qdrant_port
        self.collection_name = "organizational_memory"
        self.client = None
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http import models as qdrant_models

            url = f"http://{qdrant_host}:{qdrant_port}"
            if api_key:
                self.client = QdrantClient(url=url, api_key=api_key)
            else:
                self.client = QdrantClient(url=url)
            self._qdrant_models = qdrant_models
        except Exception:
            # qdrant-client not available or connection failed; keep client None
            self.client = None
            self._qdrant_models = None

    async def ensure_collection_exists(self) -> bool:
        """Ensure the memory collection exists in Qdrant"""
        if not self.client:
            return False
        try:
            # Create collection only if it doesn't exist
            collections = self.client.get_collections()
            names = [c.name for c in collections.collections]
            if self.collection_name not in names:
                self.client.recreate_collection(
                    collection_name=self.collection_name,
                    vectors_config=self._qdrant_models.VectorParams(
                        size=EmbeddingService.EMBEDDING_DIM,
                        distance=self._qdrant_models.Distance.COSINE,
                    ),
                )
            return True
        except Exception:
            return False

    async def store_memory(
        self,
        memory_id: str,
        content: str,
        memory_type: str,  # "decision", "action", "blocker", "transcript_segment", "insight"
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Store a memory vector in Qdrant"""
        # Generate embedding
        embedding = EmbeddingService.embed_text(content)

        if not self.client:
            # Fallback: in-memory/no-op store
            return True

        try:
            payload = {
                "memory_id": memory_id,
                "content": content,
                "memory_type": memory_type,
            }
            if metadata:
                payload.update(metadata)

            # Qdrant expects list of points with id, vector, payload
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    {
                        "id": memory_id,
                        "vector": embedding,
                        "payload": payload,
                    }
                ],
            )
            return True
        except Exception:
            return False

    async def search_similar(
        self,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 5,
        score_threshold: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        Search for semantically similar memories.
        
        Returns:
            List of similar memories with scores
        """
        query_embedding = EmbeddingService.embed_text(query)

        if not self.client:
            return []

        try:
            # Build filter if memory_type provided
            query_filter = None
            if memory_type and self._qdrant_models is not None:
                query_filter = self._qdrant_models.Filter(
                    must=[
                        self._qdrant_models.FieldCondition(
                            key="memory_type",
                            match=self._qdrant_models.MatchValue(value=memory_type),
                        )
                    ]
                )

            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                query_filter=query_filter,
            )

            out: List[Dict[str, Any]] = []
            for r in results:
                score = getattr(r, 'score', None) or r.get('score', None)
                payload = getattr(r, 'payload', None) or r.get('payload', {})
                out.append({
                    "id": getattr(r, 'id', None) or r.get('id'),
                    "payload": payload,
                    "score": float(score) if score is not None else None,
                })

            # Apply threshold filtering
            if score_threshold is not None:
                out = [o for o in out if o.get('score') is None or o['score'] >= score_threshold]

            return out
        except Exception:
            return []

    async def batch_store_memories(
        self,
        memories: List[Dict[str, Any]],
    ) -> int:
        """
        Store multiple memories in batch.
        
        Args:
            memories: List of dicts with keys: memory_id, content, memory_type, metadata
            
        Returns:
            Number of memories stored
        """
        stored_count = 0
        for memory in memories:
            success = await self.store_memory(
                memory_id=memory["memory_id"],
                content=memory["content"],
                memory_type=memory["memory_type"],
                metadata=memory.get("metadata"),
            )
            if success:
                stored_count += 1
        
        return stored_count

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory from Qdrant"""
        # TODO: Delete from Qdrant
        # self.client.delete(
        #     collection_name=self.collection_name,
        #     points_selector=PointIdsList(
        #         idxs=[hash(memory_id)],
        #     ),
        # )
        return True

    async def get_organization_memories(
        self,
        organization_id: str,
        memory_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retrieve all memories for an organization"""
        # TODO: Filter by organization_id in Qdrant
        # Similar to search_similar but with organization filter
        return []
