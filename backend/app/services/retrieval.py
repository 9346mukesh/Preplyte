"""Retrieval: top-k semantic search per JD requirement (BRD FR-04 / FR-07).

BRD FR-07: below SIMILARITY_THRESHOLD the retrieval is treated as no match;
an optional keyword / BM25 fallback catches exact technical terms that
semantic search may miss (BRD risk R-4).
"""

from __future__ import annotations

import re
from typing import List

from ..schemas import JDRequirement, RetrievalResult, ResumeChunk
from .embeddings import EmbeddingService
from .vectorstore import VectorStore


def _tokenize(text: str) -> List[str]:
    """Simple whitespace + punctuation tokenizer for BM25 fallback."""
    return re.findall(r"\w+", text.lower())


def retrieve_per_requirement(
    requirements: List[JDRequirement],
    chunks: List[ResumeChunk],
    embeddings: EmbeddingService,
    vector_store: VectorStore,
    top_k: int,
    threshold: float,
    use_keyword_fallback: bool = True,
) -> List[RetrievalResult]:
    """Retrieve top-k resume chunks per JD requirement (FR-04, FR-07).

    1. Embed all resume chunks and index them in the vector store.
    2. Embed each JD requirement and search for top-k similar chunks.
    3. Below the similarity threshold, treat as no match.
    4. BM25 fallback: if no semantic match and use_keyword_fallback, do exact
       keyword matching to catch technical terms (BRD risk R-4).
    """
    if not requirements or not chunks:
        return []

    # Stage 3: embed resume chunks (FR-03)
    chunk_texts = [c.raw_text for c in chunks]
    chunk_embeddings = embeddings.encode(chunk_texts)
    chunk_ids = [c.chunk_id for c in chunks]

    # Store resume embeddings (FR-04)
    vector_store.add(chunk_ids, chunk_embeddings)

    # Stage 4: embed JD requirements (FR-03)
    req_texts = [r.requirement_text for r in requirements]
    req_embeddings = embeddings.encode(req_texts)

    # Stage 5: retrieve top-k per requirement (FR-04, FR-07)
    results: List[RetrievalResult] = []
    for req, req_emb in zip(requirements, req_embeddings):
        # Semantic search (FR-04)
        matched_ids, matched_scores = vector_store.search(req_emb, top_k)

        # Apply similarity threshold (FR-07)
        semantic_pass = any(s >= threshold for s in matched_scores)

        # BM25 fallback for exact keyword matching (FR-07, risk R-4)
        if not semantic_pass and use_keyword_fallback and chunks:
            req_tokens = set(_tokenize(req.requirement_text))
            keyword_scores: List[float] = []
            for chunk in chunks:
                chunk_tokens = set(_tokenize(chunk.raw_text))
                overlap = req_tokens & chunk_tokens
                # Score = fraction of requirement tokens found in chunk
                score = len(overlap) / len(req_tokens) if req_tokens else 0.0
                keyword_scores.append(score)
            # Sort by keyword score descending
            sorted_indices = sorted(
                range(len(chunks)), key=lambda i: keyword_scores[i], reverse=True
            )
            # Take top_k by keyword score where score > 0
            keyword_matches = [
                (chunks[i].chunk_id, keyword_scores[i])
                for i in sorted_indices[:top_k]
                if keyword_scores[i] > 0
            ]
            if keyword_matches:
                matched_ids = [cid for cid, _ in keyword_matches]
                matched_scores = [s for _, s in keyword_matches]
                semantic_pass = True  # keyword match counts as threshold pass

        results.append(
            RetrievalResult(
                requirement_id=req.requirement_id,
                retrieved_chunk_ids=matched_ids,
                similarity_scores=matched_scores,
                threshold_pass=semantic_pass,
            )
        )

    return results
