"""Vector store abstraction (BRD section 15, NFR Maintainability).

Default implementation is in-process FAISS. pgvector / Pinecone can be
swapped in by implementing the same interface and selecting it via the
VECTOR_STORE env var.
"""

from __future__ import annotations

from typing import List, Tuple

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
    """In-process FAISS index storing normalized embeddings (cosine)."""

    def __init__(self, dimension: int = 384) -> None:
        settings = get_settings()
        self.dimension = dimension
        self._index = None
        self._ids: List[str] = []

    def add(self, ids: List[str], embeddings: List[List[float]]) -> None:
        # Planned for Day 3: build IndexFlatIP over normalized vectors.
        raise NotImplementedError(
            "FAISS indexing lands on Day 3 (retrieval milestone)"
        )

    def search(
        self, query: List[float], top_k: int
    ) -> Tuple[List[str], List[float]]:
        raise NotImplementedError(
            "FAISS search lands on Day 3 (retrieval milestone)"
        )


def build_vector_store(vector_store: Optional[str] = None) -> VectorStore:
    settings = get_settings()
    kind = (vector_store or settings.vector_store).lower()
    if kind == "faiss":
        return FAISSVectorStore()
    raise ValueError(f"Unsupported VECTOR_STORE: {kind}")
