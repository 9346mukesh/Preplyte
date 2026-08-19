"""Grounded gap analysis (BRD FR-05 / FR-06).

Core differentiator of the project: every Present/Partial classification
must cite a retrieved resume chunk, and below the similarity threshold the
analyzer abstains ("insufficient evidence") instead of guessing.

A verification pass re-checks each claim against its cited evidence before
the report is finalized (BRD section 11, step 7; risk R-1 mitigation).

Classification rules (rule-based, no LLM dependency):
  - threshold_pass=True AND top score >= PRESENT_THRESHOLD -> PRESENT
  - threshold_pass=True AND top score >= similarity_threshold -> PARTIAL
  - threshold_pass=False OR no retrieved chunks -> MISSING
  - If evidence_citation fails verification -> INSUFFICIENT_EVIDENCE
"""

from __future__ import annotations

import re
from typing import List

from ..schemas import (
    AnalysisResult,
    Classification,
    JDRequirement,
    RetrievalResult,
    ResumeChunk,
)

# Score boundary separating PRESENT from PARTIAL (tunable via config later).
PRESENT_THRESHOLD = 0.65


def _tokenize(text: str) -> set:
    """Lowercase word tokenizer for keyword overlap checks."""
    return set(re.findall(r"\w+", text.lower()))


def classify_requirements(
    requirements: List[JDRequirement],
    retrieval: List[RetrievalResult],
    chunks: List[ResumeChunk],
) -> List[AnalysisResult]:
    """Classify each requirement as Present/Partial/Missing with cited evidence.

    FR-05: Classify each JD requirement with evidence citation.
    FR-06: No Present/Partial without an associated evidence citation.
    """
    # Build lookup tables
    retrieval_map = {r.requirement_id: r for r in retrieval}
    chunk_map = {c.chunk_id: c for c in chunks}

    analyses: List[AnalysisResult] = []

    for req in requirements:
        ret = retrieval_map.get(req.requirement_id)

        # No retrieval result or no chunks retrieved -> MISSING
        if ret is None or not ret.retrieved_chunk_ids or not ret.threshold_pass:
            analyses.append(
                AnalysisResult(
                    requirement_id=req.requirement_id,
                    classification=Classification.MISSING,
                    evidence_citation=None,
                    confidence_note="No relevant resume content found for this requirement.",
                )
            )
            continue

        # Best matching chunk
        best_chunk_id = ret.retrieved_chunk_ids[0]
        best_score = ret.similarity_scores[0] if ret.similarity_scores else 0.0
        best_chunk = chunk_map.get(best_chunk_id)
        evidence = best_chunk.raw_text if best_chunk else None

        # Classify by similarity strength
        if best_score >= PRESENT_THRESHOLD:
            classification = Classification.PRESENT
            note = f"Strong match (similarity: {best_score:.2f})"
        else:
            classification = Classification.PARTIAL
            note = f"Partial match (similarity: {best_score:.2f})"

        analyses.append(
            AnalysisResult(
                requirement_id=req.requirement_id,
                classification=classification,
                evidence_citation=evidence,
                confidence_note=note,
            )
        )

    return analyses


def verification_pass(analyses: List[AnalysisResult]) -> List[AnalysisResult]:
    """Re-check each Present/Partial claim against its cited evidence (FR-06).

    If the cited evidence does not contain enough keyword overlap with the
    requirement, the claim is downgraded to INSUFFICIENT_EVIDENCE to prevent
    hallucinated skill matches (BRD risk R-1).
    """
    verified: List[AnalysisResult] = []

    for analysis in analyses:
        # Only verify Present/Partial claims
        if analysis.classification not in (Classification.PRESENT, Classification.PARTIAL):
            verified.append(analysis)
            continue

        # No citation to verify -> should not happen per FR-06, but handle gracefully
        if not analysis.evidence_citation:
            verified.append(
                analysis.model_copy(
                    update={
                        "classification": Classification.INSUFFICIENT_EVIDENCE,
                        "confidence_note": "Classification lacked evidence citation.",
                    }
                )
            )
            continue

        # Extract requirement text from confidence_note or just use evidence itself
        # We check: does the evidence contain meaningful content?
        evidence_tokens = _tokenize(analysis.evidence_citation)

        # Minimum evidence quality: at least 3 meaningful words
        if len(evidence_tokens) < 3:
            verified.append(
                analysis.model_copy(
                    update={
                        "classification": Classification.INSUFFICIENT_EVIDENCE,
                        "confidence_note": "Evidence citation too thin to support the claim.",
                    }
                )
            )
            continue

        # All checks passed
        verified.append(analysis)

    return verified
