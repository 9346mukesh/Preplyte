"""Retrieval: top-k semantic search per JD requirement (BRD FR-04 / FR-07).

BRD FR-07: below SIMILARITY_THRESHOLD the retrieval is treated as no match;
an optional keyword / BM25 fallback catches exact technical terms that
semantic search may miss (BRD risk R-4).
"""

from __future__ import annotations

from typing import List

from ..schemas import JDRequirement, RetrievalResult, ResumeChunk
from .embeddings import EmbeddingService
from .vectorstore import VectorStore


def retrieve_per_requirement(
    requirements: List[JDRequirement],
    chunks: List[ResumeChunk],
    embeddings: EmbeddingService,
    vector_store: VectorStore,
    top_k: int,
    threshold: float,
    use_keyword_fallback: bool = True,
) -> List[RetrievalResult]:
    """Retrieve top-k resume chunks per JD requirement (FR-04, FR-07)."""
    raise NotImplementedError(
        "Retrieval lands on Day 3 (embedding + vector store milestone)"
    )
