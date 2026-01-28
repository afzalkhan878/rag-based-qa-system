"""
Ultra-fast local embedding service
No internet. No downloads. <1s startup.
"""
from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np
import hashlib
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, embedding_dim: int = 384):
        self.embedding_dim = embedding_dim

    def embed_query(self, query: str):
        return self._hash_text(query)

    def embed_text(self, text: str):
        return self._hash_text(text)

    def _hash_text(self, text: str):
        vec = np.zeros(self.embedding_dim, dtype=np.float32)
        h = hashlib.sha256(text.encode()).digest()

        for i, b in enumerate(h):
            vec[i % self.embedding_dim] += b

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm

        return vec


    def embed_chunks(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.array([])

        logger.info(f"Embedding {len(texts)} chunks (local)")
        return np.vstack([self._hash_text(t) for t in texts])

    def embed_query(self, query: str) -> np.ndarray:
        if not query.strip():
            raise ValueError("Query cannot be empty")

        return self._hash_text(query)

    def get_embedding_dimension(self) -> int:
        return self.embedding_dim
