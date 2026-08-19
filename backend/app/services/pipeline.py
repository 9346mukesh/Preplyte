"""End-to-end analysis orchestrator (BRD section 11 workflow).

Stages:
  1. parse resume (FR-01)                 -- Day 1/2 (implemented)
  2. extract JD requirements (FR-02)      -- Day 2 (implemented, heuristics)
  3. embed chunks + requirements (FR-03)  -- Day 3 (implemented)
  4. store resume embeddings (FR-04)      -- Day 3 (implemented)
  5. top-k retrieval + threshold (FR-07)  -- Day 3 (implemented)
  6. grounded classification (FR-05/06)   -- Day 4 (implemented)
  7. verification pass (FR-06)            -- Day 4 (implemented)
  8. interview questions (FR-08)          -- Day 5
  9. structured report (FR-09)            -- Day 5
"""

from __future__ import annotations

import time

from ..config import get_settings
from ..schemas import Report
from .analyzer import classify_requirements, verification_pass
from .embeddings import EmbeddingService
from .ingestion import ingest_resume
from .jd_extractor import extract_requirements
from .retrieval import retrieve_per_requirement
from .vectorstore import build_vector_store


def run_analysis(content: bytes, filename: str, jd_text: str) -> Report:
    """Run the full analysis pipeline and return a Report."""
    settings = get_settings()
    started = time.perf_counter()
    warnings: list = []

    # Stage 1: parse resume into section-tagged chunks (FR-01)
    chunks = ingest_resume(
        content,
        filename,
        chunk_size=settings.chunk_size,
        overlap=settings.chunk_overlap,
        max_pages=settings.max_resume_pages,
    )

    # Stage 2: structured JD requirements (FR-02)
    requirements = extract_requirements(jd_text)

    # Stage 3-5: embeddings + vector store + retrieval (FR-03, FR-04, FR-07)
    embeddings = EmbeddingService()
    vector_store = build_vector_store()
    retrieval_results = retrieve_per_requirement(
        requirements=requirements,
        chunks=chunks,
        embeddings=embeddings,
        vector_store=vector_store,
        top_k=settings.top_k,
        threshold=settings.similarity_threshold,
        use_keyword_fallback=True,
    )

    # Stage 6: grounded classification (FR-05, FR-06)
    analyses = classify_requirements(
        requirements=requirements,
        retrieval=retrieval_results,
        chunks=chunks,
    )

    # Stage 7: verification pass (FR-06) — re-check Present/Partial claims
    analyses = verification_pass(analyses)

    warnings.append(
        "Stages 8-9 (interview questions, report assembly) "
        "land on Day 5 of the build plan."
    )

    latency_ms = (time.perf_counter() - started) * 1000.0
    return Report(
        requirements=requirements,
        retrieval=retrieval_results,
        analyses=analyses,
        latency_ms=latency_ms,
        warnings=warnings,
    )
