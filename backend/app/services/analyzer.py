"""Grounded gap analysis (BRD FR-05 / FR-06).

Core differentiator of the project: every Present/Partial classification
must cite a retrieved resume chunk, and below the similarity threshold the
analyzer abstains ("insufficient evidence") instead of guessing.

A verification pass re-checks each claim against its cited evidence before
the report is finalized (BRD section 11, step 7; risk R-1 mitigation).
"""

from __future__ import annotations

from typing import List

from ..schemas import AnalysisResult, JDRequirement, RetrievalResult


def classify_requirements(
    requirements: List[JDRequirement],
    retrieval: List[RetrievalResult],
    chunk_lookup: dict,
) -> List[AnalysisResult]:
    """Classify each requirement as Present/Partial/Missing with evidence."""
    raise NotImplementedError(
        "Grounded classification lands on Day 4 (analysis milestone)"
    )


def verification_pass(analyses: List[AnalysisResult]) -> List[AnalysisResult]:
    """Re-check each claim against its cited evidence (FR-06)."""
    raise NotImplementedError(
        "Verification pass lands on Day 4 (analysis milestone)"
    )
