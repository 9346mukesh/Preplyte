"""Retrieval: top-k semantic search per JD requirement (BRD FR-04 / FR-07).

Improved retrieval strategy:
1. Retrieve top-k candidates via semantic search
2. Rerank by combining semantic similarity with evidence quality signals
3. Apply stricter threshold — reject evidence that's just keyword lists
4. BM25 fallback only for very specific technical terms (conservative)
"""

from __future__ import annotations

import re
from typing import List, Tuple

from ..schemas import JDRequirement, RetrievalResult, ResumeChunk
from .embeddings import EmbeddingService
from .vectorstore import VectorStore

# Minimum evidence quality signals
_MIN_SENTENCES_IN_EVIDENCE = 2
_MIN_WORDS_IN_EVIDENCE = 15
_MAX_LIST_RATIO = 0.6  # if >60% of text is comma-separated items, it's a list


def _tokenize(text: str) -> List[str]:
    """Simple whitespace + punctuation tokenizer for BM25 fallback."""
    return re.findall(r"\w+", text.lower())


def _is_list_heavy(text: str) -> bool:
    """Check if text is mostly a comma-separated list (low evidence quality)."""
    # Count comma-separated segments
    segments = [s.strip() for s in text.split(",") if s.strip()]
    if len(segments) < 3:
        return False
    # If most "words" appear in comma-separated lists, it's list-heavy
    words = text.split()
    list_words = sum(len(s.split()) for s in segments)
    return list_words / max(len(words), 1) > _MAX_LIST_RATIO


def _evidence_quality_score(text: str) -> float:
    """Score evidence quality from 0.0 (poor) to 1.0 (good).

    Evidence with full sentences and context scores higher than
    raw keyword lists.
    """
    words = text.split()
    word_count = len(words)

    # Penalize very short evidence
    if word_count < 5:
        return 0.1

    # Penalize list-heavy text (skills lists without context)
    if _is_list_heavy(text):
        return 0.3

    # Count sentence-like structures (words followed by period)
    sentences = [s for s in re.split(r'[.!?]+', text) if s.strip()]
    sentence_count = len(sentences)

    # Bonus for having multiple complete sentences
    score = 0.5
    if sentence_count >= 2:
        score += 0.2
    if word_count >= 20:
        score += 0.15
    if any(word[0].isupper() for word in words if len(word) > 2):
        score += 0.1  # has proper nouns / names

    return min(score, 1.0)


def _rerank_candidates(
    candidates: List[Tuple[str, float]],
    chunk_map: dict,
    req_text: str,
) -> List[Tuple[str, float]]:
    """Rerank retrieval candidates by combining similarity with quality.

    Final score = 0.7 * similarity + 0.3 * evidence_quality
    """
    reranked = []
    req_tokens = set(_tokenize(req_text))

    for chunk_id, sim_score in candidates:
        chunk = chunk_map.get(chunk_id)
        if not chunk:
            continue

        quality = _evidence_quality_score(chunk.raw_text)

        # Penalize if chunk is just a list of skills with no context
        # (especially when the requirement is about behavior/experience)
        chunk_tokens = set(_tokenize(chunk.raw_text))
        keyword_overlap = len(req_tokens & chunk_tokens) / max(len(req_tokens), 1)

        # Boost if there's meaningful semantic overlap (not just keyword)
        combined = 0.7 * sim_score + 0.3 * quality

        # Small penalty for pure keyword matches on list-heavy text
        if _is_list_heavy(chunk.raw_text) and keyword_overlap < 0.3:
            combined *= 0.8

        reranked.append((chunk_id, combined))

    # Sort by combined score descending
    reranked.sort(key=lambda x: x[1], reverse=True)
    return reranked


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

    Strategy:
    1. Embed all resume chunks and index them in the vector store.
    2. For each JD requirement, retrieve top_k*2 candidates via semantic search.
    3. Rerank candidates by combining similarity with evidence quality.
    4. Apply similarity threshold after reranking.
    5. BM25 fallback only if semantic search finds nothing above threshold.
    """
    if not requirements or not chunks:
        return []

    # Stage 3: embed resume chunks (FR-03)
    chunk_texts = [c.raw_text for c in chunks]
    chunk_embeddings = embeddings.encode(chunk_texts)
    chunk_ids = [c.chunk_id for c in chunks]

    # Store resume embeddings (FR-04)
    vector_store.add(chunk_ids, chunk_embeddings)

    # Build chunk lookup for reranking
    chunk_map = {c.chunk_id: c for c in chunks}

    # Stage 4: embed JD requirements (FR-03)
    req_texts = [r.requirement_text for r in requirements]
    req_embeddings = embeddings.encode(req_texts)

    # Stage 5: retrieve + rerank per requirement (FR-04, FR-07)
    results: List[RetrievalResult] = []
    for req, req_emb in zip(requirements, req_embeddings):
        # Retrieve more candidates than needed for reranking
        retrieve_k = min(top_k * 3, len(chunks))
        matched_ids, matched_scores = vector_store.search(req_emb, retrieve_k)

        if not matched_ids:
            results.append(
                RetrievalResult(
                    requirement_id=req.requirement_id,
                    retrieved_chunk_ids=[],
                    similarity_scores=[],
                    threshold_pass=False,
                )
            )
            continue

        # Rerank by similarity + evidence quality
        candidates = list(zip(matched_ids, matched_scores))
        reranked = _rerank_candidates(candidates, chunk_map, req.requirement_text)

        # Take top_k after reranking
        final_ids = [cid for cid, _ in reranked[:top_k]]
        final_scores = [s for _, s in reranked[:top_k]]

        # Apply threshold on the best reranked score
        semantic_pass = any(s >= threshold for s in final_scores)

        # Conservative BM25 fallback: only if semantic search found nothing
        if not semantic_pass and use_keyword_fallback:
            # Only match on very specific technical terms (3+ char words)
            tech_terms = [
                t for t in _tokenize(req.requirement_text) if len(t) >= 3
            ]
            if tech_terms:
                keyword_matches = []
                for chunk in chunks:
                    chunk_tokens = set(_tokenize(chunk.raw_text))
                    matched_terms = set(tech_terms) & chunk_tokens
                    # Require at least 2 specific terms to match
                    if len(matched_terms) >= 2:
                        score = len(matched_terms) / len(tech_terms)
                        keyword_matches.append((chunk.chunk_id, score))

                if keyword_matches:
                    keyword_matches.sort(key=lambda x: x[1], reverse=True)
                    final_ids = [cid for cid, _ in keyword_matches[:top_k]]
                    final_scores = [s for _, s in keyword_matches[:top_k]]
                    semantic_pass = True

        results.append(
            RetrievalResult(
                requirement_id=req.requirement_id,
                retrieved_chunk_ids=final_ids,
                similarity_scores=final_scores,
                threshold_pass=semantic_pass,
            )
        )

    return results
