"""Vector store abstraction (BRD section 15, NFR Maintainability).

Default implementation is in-process FAISS. pgvector / Pinecone can be
swapped in by implementing the same interface and selecting it via the
VECTOR_STORE env var.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import faiss
import numpy as np

from ..config import get_settings


class VectorStore:
    """Interface for vector storage and similarity search (FR-04)."""

    def add(self, ids: List[str], embeddings: List[List[float]]) -> None:
        raise NotImplementedError("VectorStore.add not implemented")

    def search(
        self, query: List[float], top_k: int
    ) -> Tuple[List[str], List[float]]:
        """Return (ids, scores) of the top-k most similar entries."""
        raise NotImplementedError("VectorStore.search not implemented")

    def save(self, path: str) -> None:
        raise NotImplementedError("VectorStore.save not implemented")

    def load(self, path: str) -> None:
        raise NotImplementedError("VectorStore.load not implemented")


class FAISSVectorStore(VectorStore):
    """In-process FAISS index storing normalized embeddings (cosine).

    Uses IndexFlatIP for inner-product (cosine similarity on normalized vectors).
    FR-04: Store resume embeddings and retrieve top-k most relevant chunks.
    """

    def __init__(self, dimension: int = 384) -> None:
        settings = get_settings()
        self.dimension = dimension
        self._index: Optional[faiss.IndexFlatIP] = None
        self._ids: List[str] = []

    def add(self, ids: List[str], embeddings: List[List[float]]) -> None:
        """Add embeddings with their IDs to the index (FR-04)."""
        if not ids:
            return
        if self._index is None:
            self._index = faiss.IndexFlatIP(self.dimension)
        vectors = np.array(embeddings, dtype=np.float32)
        self._index.add(vectors)
        self._ids.extend(ids)

    def search(
        self, query: List[float], top_k: int
    ) -> Tuple[List[str], List[float]]:
        """Return (ids, scores) of the top-k most similar entries (FR-04, FR-07)."""
        if self._index is None or self._index.ntotal == 0:
            return [], []
        query_vec = np.array([query], dtype=np.float32)
        k = min(top_k, self._index.ntotal)
        scores, indices = self._index.search(query_vec, k)
        matched_ids = [self._ids[i] for i in indices[0] if i != -1]
        matched_scores = [float(s) for s, i in zip(scores[0], indices[0]) if i != -1]
        return matched_ids, matched_scores


def build_vector_store(vector_store: Optional[str] = None) -> VectorStore:
    settings = get_settings()
    kind = (vector_store or settings.vector_store).lower()
    if kind == "faiss":
        return FAISSVectorStore()
    raise ValueError(f"Unsupported VECTOR_STORE: {kind}")
